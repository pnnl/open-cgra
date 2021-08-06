/*
 * ======================================================================
 * DFG.cpp
 * ======================================================================
 * DFG implementation.
 *
 * Author : Cheng Tan
 *   Date : July 16, 2019
 */

#include <fstream>
#include "DFG.h"

DFG::DFG(Function& t_F, list<Loop*>* t_loops, bool t_heterogeneity) {
  m_num = 0;
  m_targetLoops = t_loops;
  m_orderedNodes = NULL;
  construct(t_F);
  tuneForBranch();
  tuneForBitcast();
  tuneForLoad();
  if (t_heterogeneity) {
    getCycles();
//    combine("phi", "add");
//    combine("and", "xor");
//    combine("br", "phi");
//    combine("add", "icmp");
//    combine("xor", "add");
    combineCmpBranch();
//    combine("icmp", "br");
//    combine("getelementptr", "load");
    tuneForPattern();

//    getCycles();
////    combine("icmp", "br");
//    combine("xor", "add");
//    tuneForPattern();
  }
  trimForStandalone();
}

// FIXME: only combine operations of mul+alu and alu+cmp for now,
//        since these two are the most common patterns across all
//        the kernels.
void DFG::tuneForPattern() {

  // reconstruct connected DFG by modifying m_DFGEdge
  list<DFGNode*>* removeNodes = new list<DFGNode*>();
  for (DFGNode* dfgNode: nodes) {
    if (dfgNode->hasCombined()) {
      if (dfgNode->isPatternRoot()) {
        for (DFGNode* patternNode: *(dfgNode->getPatternNodes())) {
          if (hasDFGEdge(dfgNode, patternNode))
            m_DFGEdges.remove(getDFGEdge(dfgNode, patternNode));
          for (DFGNode* predNode: *(patternNode->getPredNodes())) {
            if (predNode == dfgNode or
                predNode->isOneOfThem(dfgNode->getPatternNodes())) {
              deleteDFGEdge(predNode, patternNode);
              continue;
            }
            DFGNode* newPredNode = NULL;
            if (predNode->hasCombined())
              newPredNode = predNode->getPatternRoot();
            else
              newPredNode = predNode;
            replaceDFGEdge(predNode, patternNode, newPredNode, dfgNode);
          }
          for (DFGNode* succNode: *(patternNode->getSuccNodes())) {
            if (succNode == dfgNode or
                succNode->isOneOfThem(dfgNode->getPatternNodes())) {
              deleteDFGEdge(patternNode, succNode);
              continue;
            }
            DFGNode* newSuccNode = NULL;
            if (succNode->hasCombined())
              newSuccNode = succNode->getPatternRoot();
            else
              newSuccNode = succNode;
            replaceDFGEdge(patternNode, succNode, dfgNode, newSuccNode);
          }

        }
      } else {
        removeNodes->push_back(dfgNode);
      }
    }
  }
  for (DFGNode* dfgNode: *removeNodes) {
    nodes.remove(dfgNode);
  }
}

void DFG::combineCmpBranch() {
  // detect patterns (e.g., cmp+branch)
  DFGNode* addNode = NULL;
  DFGNode* cmpNode = NULL;
  DFGNode* brhNode = NULL;
  bool found = false;
  for (DFGNode* dfgNode: nodes) {
    if (dfgNode->isAdd() and !dfgNode->hasCombined()) {
      found = false;
      for (DFGNode* succNode: *(dfgNode->getSuccNodes())) {
        if (succNode->isCmp() and !succNode->hasCombined()) {
          for (DFGNode* succSuccNode: *(succNode->getSuccNodes())) {
            if (succSuccNode->isBranch() and !succSuccNode->hasCombined() and
                succSuccNode->isSuccessorOf(dfgNode)) {
              addNode = dfgNode;
              addNode->setCombine();
              cmpNode = succNode;
              addNode->addPatternPartner(cmpNode);
              cmpNode->setCombine();
              brhNode = succSuccNode;
              addNode->addPatternPartner(brhNode);
              brhNode->setCombine();
              found = true;
              break;
            }
          }
        }
        if (found) break;
      }
    }
  }
}

void DFG::combineMulAdd() {
  // detect patterns (e.g., mul+alu)
  DFGNode* mulNode = NULL;
  DFGNode* addNode = NULL;
  bool found = false;
  for (DFGNode* dfgNode: nodes) {
    if (dfgNode->isMul() and dfgNode->isCritical() and !dfgNode->hasCombined()) {
      for (DFGNode* succNode: *(dfgNode->getSuccNodes())) {
        if (succNode->isAdd() and succNode->isCritical() and !succNode->hasCombined()) {
          mulNode = dfgNode;
          mulNode->setCombine();
          addNode = succNode;
          mulNode->addPatternPartner(addNode);
          addNode->setCombine();
          break;
        }
      }
    }
  }
}

void DFG::combine(string t_opt0, string t_opt1) {
  DFGNode* opt0Node = NULL;
  DFGNode* opt1Node = NULL;
  bool found = false;
  for (DFGNode* dfgNode: nodes) {
//    if (dfgNode->isOpt(t_opt0) and dfgNode->isCritical() and !dfgNode->hasCombined()) {
    if (dfgNode->isOpt(t_opt0) and !dfgNode->hasCombined()) {
      for (DFGNode* succNode: *(dfgNode->getSuccNodes())) {
        if (succNode->isOpt(t_opt1) and !succNode->hasCombined()) {
          opt0Node = dfgNode;
          opt0Node->setCombine();
          opt1Node = succNode;
          opt0Node->addPatternPartner(opt1Node);
          opt1Node->setCombine();
          break;
        }
      }
    }
  }
}

bool DFG::shouldIgnore(Instruction* t_inst) {
  if (m_targetLoops->size() == 0)
    return false;
  for (Loop* current_loop: *m_targetLoops) {
    if (current_loop->contains(t_inst)) {
      return false;
    }
  }
  return true;
}

list<DFGNode*>* DFG::getDFSOrderedNodes() {
  if (m_orderedNodes != NULL)
    return m_orderedNodes;
  m_orderedNodes = new list<DFGNode*>();
  list<DFGNode*> tempNodes;
  while (m_orderedNodes->size() < nodes.size()) {
    DFGNode* startNode = NULL;
    int curWithMaxSucc = 0;
    for (DFGNode* dfgNode: nodes) {
      if (find(m_orderedNodes->begin(), m_orderedNodes->end(), dfgNode) ==
          m_orderedNodes->end()) {
        if (dfgNode->getSuccNodes()->size() > curWithMaxSucc) {
          curWithMaxSucc = dfgNode->getSuccNodes()->size();
          startNode = dfgNode;
        }
      }
    }
    if (startNode != NULL) {
      assert( find(m_orderedNodes->begin(), m_orderedNodes->end(), startNode) ==
          m_orderedNodes->end() );
      tempNodes.push_back(startNode);
      m_orderedNodes->push_back(startNode);
    }
//    for (DFGNode* dfgNode: nodes) {
//      if (find(m_orderedNodes->begin(), m_orderedNodes->end(), dfgNode) ==
//          m_orderedNodes->end()) {
//        tempNodes.push_back(dfgNode);
//        m_orderedNodes->push_back(dfgNode);
//        break;
//      }
//    }
    DFGNode* currentNode;
    while (tempNodes.size() != 0) {
      currentNode = tempNodes.back();
      list<DFGNode*>* succNodes = currentNode->getSuccNodes();
      bool canPop = true;
      for (DFGNode* succNode: *succNodes) {
        if (find(m_orderedNodes->begin(), m_orderedNodes->end(), succNode) ==
            m_orderedNodes->end()) {
          tempNodes.push_back(succNode);
          canPop = false;
          m_orderedNodes->push_back(succNode);
          break;
        }
      }
      if (canPop) {
        tempNodes.pop_back();
      }
    }
  }
  errs()<<"\nordered nodes: \n";
  for (DFGNode* dfgNode: *m_orderedNodes) {
    errs()<<dfgNode->getID()<<"  ";
  }
  errs()<<"\n";
  assert(m_orderedNodes->size() == nodes.size());
  return m_orderedNodes;
}

list<DFGNode*>* DFG::getBFSOrderedNodes() {
  if (m_orderedNodes != NULL)
    return m_orderedNodes;
  m_orderedNodes = new list<DFGNode*>();
  list<DFGNode*> tempNodes;
  while (m_orderedNodes->size() < nodes.size()) {
    for (DFGNode* dfgNode: nodes) {
      if (find(m_orderedNodes->begin(), m_orderedNodes->end(), dfgNode) ==
            m_orderedNodes->end()) {
        tempNodes.push_back(dfgNode);
        m_orderedNodes->push_back(dfgNode);
        break;
      }
    }
    DFGNode* currentNode;
    while (tempNodes.size() != 0) {
      currentNode = tempNodes.front();
      tempNodes.pop_front();
      for (DFGNode* succNode: *currentNode->getSuccNodes()) {
        if (find(m_orderedNodes->begin(), m_orderedNodes->end(), succNode) ==
            m_orderedNodes->end()) {
          tempNodes.push_back(succNode);
          m_orderedNodes->push_back(succNode);
        }
      }
    }
  }
  errs()<<"\nordered nodes: \n";
  for (DFGNode* dfgNode: *m_orderedNodes) {
    errs()<<dfgNode->getID()<<"  ";
  }
  errs()<<"\n";
  assert(m_orderedNodes->size() == nodes.size());
  return m_orderedNodes;
}

// extract DFG from specific function
void DFG::construct(Function& t_F) {

  m_DFGEdges.clear();
  nodes.clear();
  m_ctrlEdges.clear();

  int nodeID = 0;
  int ctrlEdgeID = 0;
  int dfgEdgeID = 0;

  errs()<<"*** current function: "<<t_F.getName()<<"\n";

  // FIXME: eleminate duplicated edges.
  for (Function::iterator BB=t_F.begin(), BEnd=t_F.end();
      BB!=BEnd; ++BB) {
    BasicBlock *curBB = &*BB;
    errs()<<"*** current basic block: "<<*curBB->begin()<<"\n";

     // Construct DFG nodes.
    for (BasicBlock::iterator II=curBB->begin(),
        IEnd=curBB->end(); II!=IEnd; ++II) {
      Instruction* curII = &*II;

      // Ignore this IR if it is out of the scope.
      if (shouldIgnore(curII)) {
//        errs()<<"*** ignored by pass due to that the BB is out "<<
//            "of the scope (target loop)\n";
        continue;
      }
      errs()<<*curII<<"\n";
      DFGNode* dfgNode;
      if (hasNode(curII)) {
        dfgNode = getNode(curII);
      } else {
        dfgNode = new DFGNode(nodeID++, curII, getValueName(curII));
        nodes.push_back(dfgNode);
      }
    }
    Instruction* terminator = curBB->getTerminator();

    if (shouldIgnore(terminator))
      continue;
//    DFGNode* dfgNodeTerm = new DFGNode(nodeID++, terminator, getValueName(terminator));
    for (BasicBlock* sucBB : successors(curBB)) {
      for (BasicBlock::iterator II=sucBB->begin(),
          IEnd=sucBB->end(); II!=IEnd; ++II) {
        Instruction* inst = &*II;
//      for (Instruction* inst: sucBB) {
        // Ignore this IR if it is out of the scope.
        if (shouldIgnore(inst))
          continue;
        DFGNode* dfgNode;
        if (hasNode(inst)) {
          dfgNode = getNode(inst);
        } else {
          dfgNode = new DFGNode(nodeID++, inst, getValueName(inst));
          nodes.push_back(dfgNode);
        }
//        Instruction* first = &*(sucBB->begin());
        if (!getNode(inst)->isPhi())
          continue;

        // Construct contrl flow edges.
        DFGEdge* ctrlEdge;
        if (hasCtrlEdge(getNode(terminator), dfgNode)) {
          ctrlEdge = getCtrlEdge(getNode(terminator), dfgNode);
        }
        else {
          ctrlEdge = new DFGEdge(ctrlEdgeID++, getNode(terminator), dfgNode);
          m_ctrlEdges.push_back(ctrlEdge);
        }
      }
    }
  }

//  // Construct contrl flow forward edges.
//  for (list<DFGNode*>::iterator nodeItr=nodes.begin();
//      nodeItr!=nodes.end(); ++nodeItr) {
//    list<DFGNode*>::iterator next = nodeItr;
//    ++next;
//    if (next != nodes.end()) {
//      DFGEdge* ctrlEdge;
//      if (hasCtrlEdge(*nodeItr, *next))
//        ctrlEdge = getCtrlEdge(*nodeItr, *next);
//      else {
//        ctrlEdge = new DFGEdge(ctrlEdgeID++, *nodeItr, *next);
//        m_ctrlEdges.push_back(ctrlEdge);
//      }
//    }
//  }

  // Construct data flow edges.
  for (DFGNode* node: nodes) {
//    nodes.push_back(Node(curII, getValueName(curII)));
    Instruction* curII = node->getInst();
    assert(node == getNode(curII));
    switch (curII->getOpcode()) {
      // The load/store instruction is special
      case llvm::Instruction::Load: {
        LoadInst* linst = dyn_cast<LoadInst>(curII);
        Value* loadValPtr = linst->getPointerOperand();

        // Parameter of the loop or the basic block, invisible in DFG.
        if (!hasNode(loadValPtr))
          break;
        DFGEdge* dfgEdge;
        if (hasDFGEdge(getNode(loadValPtr), node))
          dfgEdge = getDFGEdge(getNode(loadValPtr), node);
        else {
          dfgEdge = new DFGEdge(dfgEdgeID++, getNode(loadValPtr), node);
          m_DFGEdges.push_back(dfgEdge);
        }
//        getNode(loadValPtr)->setOutEdge(dfgEdge);
//        (*nodeItr)->setInEdge(dfgEdge);
        break;
      }
      case llvm::Instruction::Store: {
        StoreInst* sinst = dyn_cast<StoreInst>(curII);
        Value* storeValPtr = sinst->getPointerOperand();
        Value* storeVal = sinst->getValueOperand();
        DFGEdge* dfgEdge1;
        DFGEdge* dfgEdge2;

        // TODO: need to figure out storeVal and storeValPtr
        if (hasNode(storeVal)) {
          if (hasDFGEdge(getNode(storeVal), node))
            dfgEdge1 = getDFGEdge(getNode(storeVal), node);
          else {
            dfgEdge1 = new DFGEdge(dfgEdgeID++, getNode(storeVal), node);
            m_DFGEdges.push_back(dfgEdge1);
          }
//          getNode(storeVal)->setOutEdge(dfgEdge1);
//          (*nodeItr)->setInEdge(dfgEdge1);
        }
        if (hasNode(storeValPtr)) {
//          if (hasDFGEdge(*nodeItr, getNode(storeValPtr)))
          if (hasDFGEdge(getNode(storeValPtr), node))
//            dfgEdge2 = getDFGEdge(*nodeItr, getNode(storeValPtr));
            dfgEdge2 = getDFGEdge(getNode(storeValPtr), node);
          else {
//            dfgEdge2 = new DFGEdge(dfgEdgeID++, *nodeItr, getNode(storeValPtr));
            dfgEdge2 = new DFGEdge(dfgEdgeID++, getNode(storeValPtr), node);
            m_DFGEdges.push_back(dfgEdge2);
          }
//          getNode(storeValPtr)->setOutEdge(dfgEdge2);
//          (*nodeItr)->setInEdge(dfgEdge2);
//          (*nodeItr)->setOutEdge(dfgEdge2);
//          getNode(storeValPtr)->setInEdge(dfgEdge2);
        }
        break;
      }
      default: {
        for (Instruction::op_iterator op = curII->op_begin(), opEnd = curII->op_end(); op != opEnd; ++op) {
          Instruction* tempInst = dyn_cast<Instruction>(*op);
          if (tempInst and !shouldIgnore(tempInst)) {
            if(node->isBranch()) {
              errs()<<"real branch's pred: "<<*tempInst<<"\n";
            }
            DFGEdge* dfgEdge;
            if (hasNode(tempInst)) {
              if (hasDFGEdge(getNode(tempInst), node))
                dfgEdge = getDFGEdge(getNode(tempInst), node);
              else {
                dfgEdge = new DFGEdge(dfgEdgeID++, getNode(tempInst), node);
                m_DFGEdges.push_back(dfgEdge);
              }
//              getNode(tempInst)->setOutEdge(dfgEdge);
//              (*nodeItr)->setInEdge(dfgEdge);
            }
          } else {
            // Original Branch node will take three
            // predecessors (i.e., condi, true, false).
            if(!node->isBranch())
              node->addConst();
          } 
        }
        break;
      }
    }
  }
  connectDFGNodes();
}

void DFG::connectDFGNodes() {
  for (DFGNode* node: nodes)
    node->cutEdges();

  for (DFGEdge* edge: m_DFGEdges) {
    DFGNode* left = edge->getSrc();
    DFGNode* right = edge->getDst();
    left->setOutEdge(edge);
    right->setInEdge(edge);
  }
}

void DFG::generateJSON() {
  ofstream jsonFile;
  jsonFile.open("dfg.json");
  jsonFile<<"[\n";
  int node_index = 0;
  int node_size = nodes.size();
  for (DFGNode* node: nodes) {
    jsonFile<<"  {\n";
    jsonFile<<"    \"fu\"         : \""<<node->getFuType()<<"\",\n";
    jsonFile<<"    \"id\"         : "<<node->getID()<<",\n";
    jsonFile<<"    \"org_opt\"    : \""<<node->getOpcodeName()<<"\",\n";
    jsonFile<<"    \"JSON_opt\"   : \""<<node->getJSONOpt()<<"\",\n";
    jsonFile<<"    \"in_const\"   : [";
    int const_size = node->getNumConst();
    for (int const_index=0; const_index < const_size; ++const_index) {
      jsonFile<<const_index;
      if (const_index < const_size - 1)
        jsonFile<<",";
    }
    jsonFile<<"],\n";
    jsonFile<<"    \"pre\"         : [";
    int in_size = node->getPredNodes()->size();
    int in_index = 0;
    for (DFGNode* predNode: *(node->getPredNodes())) {
      jsonFile<<predNode->getID();
      in_index += 1;
      if (in_index < in_size)
        jsonFile<<",";
    }
    jsonFile<<"],\n";
    jsonFile<<"    \"succ\"       : [[";
    int out_size = node->getSuccNodes()->size();
    int out_index = 0;
    for (DFGNode* succNode: *(node->getSuccNodes())) {
      jsonFile<<succNode->getID();
      out_index += 1;
      if (out_index < out_size)
        jsonFile<<",";
    }
    jsonFile<<"]]\n";
    node_index += 1;
    if (node_index < node_size)
      jsonFile<<"  },\n";
    else
      jsonFile<<"  }\n";
  }
  jsonFile<<"]\n";
}

void DFG::generateDot(Function &t_F, bool t_isTrimmedDemo) {

  error_code error;
//  sys::fs::OpenFlags F_Excl;
  StringRef fileName(t_F.getName().str() + ".dot");
  raw_fd_ostream file(fileName, error, sys::fs::F_None);

  file << "digraph \"DFG for'" + t_F.getName() + "\' function\" {\n";

  //Dump DFG nodes.
  for (DFGNode* node: nodes) {
//    if (dyn_cast<Instruction>((*node)->getInst())) {
    if (t_isTrimmedDemo) {
      file << "\tNode" << node->getID() << node->getOpcodeName() << "[shape=record, label=\"" << "(" << node->getID() << ") " << node->getOpcodeName() << "\"];\n";
    } else {
      file << "\tNode" << node->getInst() << "[shape=record, label=\"" <<
          changeIns2Str(node->getInst()) << "\"];\n";
    }
  }
  /*
    if(dyn_cast<Instruction>(node->first))
      file << "\tNode" << node->first << "[shape=record, label=\"" << *(node->first) << "\"];\n";
      file << "\tNode" << (*node)->getInst() << "[shape=record, label=\"" << ((*node)->getID()) << "\"];\n";
    else {
      file << "\tNode" << (*node)->getInst() << "[shape=record, label=\"" << (*node)->getStringRef() << "\"];\n";
    }
            file << "\tNode" << node->first << "[shape=record, label=\"" << node->second << "\"];\n";
  */

  /*
  //Dump control flow.
  for (list<DFGEdge*>::iterator edge = m_ctrlEdges.begin(), edge_end = m_ctrlEdges.end(); edge != edge_end; ++edge) {
    file << "\tNode" << (*edge)->getSrc()->getID() << "_" << (*edge)->getSrc()->getOpcodeName() << " -> Node" << (*edge)->getDst()->getID() << "_" << (*edge)->getDst()->getOpcodeName() << "\n";
//    file << "\tNode" << (*edge)->getSrc()->getInst() << " -> Node" << (*edge)->getDst()->getInst() << "\n";
  // file << "\tNode" << edge->first.first << " -> Node" << edge->second.first << "\n";
  }
  */

  //Dump data flow.
  file << "edge [color=red]" << "\n";
  for (DFGEdge* edge: m_DFGEdges) {
    if (t_isTrimmedDemo) {
      file << "\tNode" << edge->getSrc()->getID() << edge->getSrc()->getOpcodeName() << " -> Node" << edge->getDst()->getID() << edge->getDst()->getOpcodeName() << "\n";
    } else {
      file << "\tNode" << edge->getSrc()->getInst() << " -> Node" << edge->getDst()->getInst() << "\n";
    }
  }
//  errs() << "Write data flow done.\n";
  file << "}\n";
  file.close();

}

void DFG::DFS_on_DFG(DFGNode* t_head, DFGNode* t_current,
    list<DFGEdge*>* t_erasedEdges, list<DFGEdge*>* t_currentCycle,
    list<list<DFGEdge*>*>* t_cycles) {
  int times = 0;
  for (DFGEdge* edge: m_DFGEdges) {
    times++;
    if (find(t_erasedEdges->begin(), t_erasedEdges->end(), edge) != t_erasedEdges->end())
      continue;
    // check whether the IR is equal
    if (edge->getSrc() == t_current) {
      // skip the visited nodes/edges:
      if (find(t_currentCycle->begin(), t_currentCycle->end(), edge) != t_currentCycle->end()) {
        continue;
      }
      t_currentCycle->push_back(edge);
      if (edge->getDst() == t_head) {
        errs() << "==================================\n";
        errs() << "[detected one cycle]\n";
        list<DFGEdge*>* temp_cycle = new list<DFGEdge*>();
        for (DFGEdge* currentEdge: *t_currentCycle) {
          temp_cycle->push_back(currentEdge);
          // break the cycle to avoid future repeated detection
          errs() << "cycle edge: {" << *(currentEdge)->getSrc()->getInst() << "  } -> {"<< *(currentEdge)->getDst()->getInst() << "  }\n";
        }
        t_erasedEdges->push_back(edge);
        t_cycles->push_back(temp_cycle);
      } else {
        DFS_on_DFG(t_head, edge->getDst(), t_erasedEdges, t_currentCycle, t_cycles);
      }
    }
  }
  if (t_currentCycle->size()!=0) {
    t_currentCycle->pop_back();
  }
}

list<list<DFGEdge*>*>* DFG::getCycles() {
  list<list<DFGEdge*>*>* cycleLists = new list<list<DFGEdge*>*>();
  list<DFGEdge*>* currentCycle = new list<DFGEdge*>();
  list<DFGEdge*>* erasedEdges = new list<DFGEdge*>();
  cycleLists->clear();
  for (DFGNode* node: nodes) {
    currentCycle->clear();
    DFS_on_DFG(node, node, erasedEdges, currentCycle, cycleLists);
  }
  for (list<DFGEdge*>* cycle: *cycleLists) {
    for (DFGEdge* edge: *cycle) {
      edge->getDst()->setCritical();
    }
  }
  return cycleLists;
}

void DFG::showOpcodeDistribution() {

  map<string, int> opcodeMap;
  for (DFGNode* node: nodes) {
    opcodeMap[node->getOpcodeName()] += 1;
  }
  for (map<string, int>::iterator opcodeItr=opcodeMap.begin();
      opcodeItr!=opcodeMap.end(); ++opcodeItr) {
    errs() << (*opcodeItr).first << " : " << (*opcodeItr).second << "\n";
  }
}

int DFG::getID(DFGNode* t_node) {
  int index = 0;
  return t_node->getID();
}

DFGNode* DFG::getNode(Value* t_value) {
  for (DFGNode* node: nodes) {
    if (node->getInst() == t_value) {
      return node;
    }
  }
  assert("ERROR cannot find the corresponding DFG node.");
  return NULL;
}

bool DFG::hasNode(Value* t_value) {
  for (DFGNode* node: nodes) {
    if (node->getInst() == t_value) {
      return true;
    }
  }
  return false;
}

DFGEdge* DFG::getCtrlEdge(DFGNode* t_src, DFGNode* t_dst) {
  for (DFGEdge* edge: m_ctrlEdges) {
    if (edge->getSrc() == t_src and
        edge->getDst() == t_dst) {
      return edge;
    }
  }
  assert("ERROR cannot find the corresponding Ctrl edge.");
  return NULL;
}

bool DFG::hasCtrlEdge(DFGNode* t_src, DFGNode* t_dst) {
  for (DFGEdge* edge: m_ctrlEdges) {
    if (edge->getSrc() == t_src and
        edge->getDst() == t_dst) {
      return true;
    }
  }
  return false;
}

DFGEdge* DFG::getDFGEdge(DFGNode* t_src, DFGNode* t_dst) {
  for (DFGEdge* edge: m_DFGEdges) {
    if (edge->getSrc() == t_src and
        edge->getDst() == t_dst) {
      return edge;
    }

  }
  assert("ERROR cannot find the corresponding DFG edge.");
  return NULL;
}

void DFG::replaceDFGEdge(DFGNode* t_old_src, DFGNode* t_old_dst,
                         DFGNode* t_new_src, DFGNode* t_new_dst) {
  DFGEdge* target = NULL;
  errs()<<"replace edge: [delete] "<<t_old_src->getID()<<"->"<<t_old_dst->getID()<<" [new] "<<t_new_src->getID()<<"->"<<t_new_dst->getID()<<"\n";
  for (DFGEdge* edge: m_DFGEdges) {
    if (edge->getSrc() == t_old_src and
        edge->getDst() == t_old_dst) {
      target = edge;
      break;
    }
  }
  if (target == NULL)
    assert("ERROR cannot find the corresponding DFG edge.");
  m_DFGEdges.remove(target);
  DFGEdge* newEdge = new DFGEdge(target->getID(), t_new_src, t_new_dst);
  m_DFGEdges.push_back(newEdge);
}

void DFG::deleteDFGEdge(DFGNode* t_src, DFGNode* t_dst) {
  if (!hasDFGEdge(t_src, t_dst)) return;
  m_DFGEdges.remove(getDFGEdge(t_src, t_dst));
}

bool DFG::hasDFGEdge(DFGNode* t_src, DFGNode* t_dst) {
  for (DFGEdge* edge: m_DFGEdges) {
    if (edge->getSrc() == t_src and
        edge->getDst() == t_dst) {
      return true;
    }
  }
  return false;
}

string DFG::changeIns2Str(Instruction* t_ins) {
  string temp_str;
  raw_string_ostream os(temp_str);
  t_ins->print(os);
  return os.str();
}

//get value's name or inst's content
StringRef DFG::getValueName(Value* t_value) {
  string temp_result = "val";
  if (t_value->getName().empty()) {
    temp_result += to_string(m_num);
    m_num++;
  }
  else {
    temp_result = t_value->getName().str();
  }
  StringRef result(temp_result);
//  errs() << "" << result;
  return result;
}

int DFG::getNodeCount() {
  return nodes.size();
}

void DFG::tuneForBitcast() {
  list<DFGNode*> unnecessaryDFGNodes;
  list<DFGEdge*> replaceDFGEdges;
  list<DFGEdge*> newDFGEdges;
  for (DFGNode* dfgNode: nodes) {
    if (dfgNode->isBitcast()) {
      unnecessaryDFGNodes.push_back(dfgNode);
      list<DFGNode*>* predNodes = dfgNode->getPredNodes();
      for (DFGNode* predNode: *predNodes) {
        replaceDFGEdges.push_back(getDFGEdge(predNode, dfgNode));
      }
      list<DFGNode*>* succNodes = dfgNode->getSuccNodes();
      for (DFGNode* succNode: *succNodes) {
        replaceDFGEdges.push_back(getDFGEdge(dfgNode, succNode));
        for (DFGNode* predNode: *predNodes) {
          DFGEdge* bypassDFGEdge = new DFGEdge(predNode->getID(),
              predNode, succNode);
          newDFGEdges.push_back(bypassDFGEdge);
        }
      }
    }
  }

  for (DFGNode* dfgNode: unnecessaryDFGNodes)
    nodes.remove(dfgNode);

  for (DFGEdge* dfgEdge: replaceDFGEdges)
    m_DFGEdges.remove(dfgEdge);

  for (DFGEdge* dfgEdge: newDFGEdges)
    m_DFGEdges.push_back(dfgEdge);

  connectDFGNodes();
}

void DFG::tuneForLoad() {
  list<DFGNode*> unnecessaryDFGNodes;
  list<DFGEdge*> removeDFGEdges;
  list<DFGEdge*> newDFGEdges;
  for (DFGNode* dfgNode: nodes) {
    if (dfgNode->isGetptr()) {
      list<DFGNode*>* succNodes = dfgNode->getSuccNodes();
      DFGNode* firstLoadNode = NULL;
      for (DFGNode* succNode: *succNodes) {
        if (firstLoadNode == NULL and succNode->isLoad()) {
          firstLoadNode = succNode;
        } else if (firstLoadNode != NULL and succNode->isLoad()) {
          unnecessaryDFGNodes.push_back(succNode);
          removeDFGEdges.push_back(getDFGEdge(dfgNode, succNode));
          for (DFGNode* succOfLoad: *(succNode->getSuccNodes())) {
            DFGEdge* removeEdge = getDFGEdge(succNode, succOfLoad);
            removeDFGEdges.push_back(removeEdge);
            DFGEdge* newDFGEdge = new DFGEdge(removeEdge->getID(),
                firstLoadNode, succOfLoad);
            newDFGEdges.push_back(newDFGEdge);
          }
        }
      }
    }
  }

  for (DFGNode* dfgNode: unnecessaryDFGNodes)
    nodes.remove(dfgNode);

  for (DFGEdge* dfgEdge: removeDFGEdges)
    m_DFGEdges.remove(dfgEdge);

  for (DFGEdge* dfgEdge: newDFGEdges)
    m_DFGEdges.push_back(dfgEdge);

  connectDFGNodes();
}

// This is necessary to handle the control flow.
// Each one would have their own implementation about control
// flow handling. We simply connect 'br' to the entry ('phi')
// of the corresponding basic blocks (w/o including additional
// DFG nodes).
void DFG::tuneForBranch() {
  list<DFGNode*> processedDFGBrNodes;
  list<DFGEdge*> replaceDFGEdges;
  list<DFGEdge*> newBrDFGEdges;
  int newDFGEdgeID = m_DFGEdges.size();
  for (DFGEdge* dfgEdge: m_ctrlEdges) {
    DFGNode* left = dfgEdge->getSrc();
    DFGNode* right = dfgEdge->getDst();
    assert(left->isBranch());
    assert(right->isPhi());
    if (find(processedDFGBrNodes.begin(), processedDFGBrNodes.end(), left) ==
        processedDFGBrNodes.end()) {
      processedDFGBrNodes.push_back(left);
    } else {
      DFGNode* newDFGBrNode = new DFGNode(nodes.size(), left->getInst(),
          getValueName(left->getInst()));
      for (DFGNode* predDFGNode: *(left->getPredNodes())) {
        DFGEdge* newDFGBrEdge = new DFGEdge(newDFGEdgeID++,
            predDFGNode, newDFGBrNode);
        m_DFGEdges.push_back(newDFGBrEdge);
      }
      nodes.push_back(newDFGBrNode);
      left = newDFGBrNode;
    }
    list<DFGNode*>* predNodes = right->getPredNodes();
    for (DFGNode* predNode: *predNodes) {
      DFGEdge* replaceDFGEdge = getDFGEdge(predNode, right);
      DFGEdge* brDataDFGEdge = new DFGEdge(replaceDFGEdge->getID(), predNode, left);
      DFGEdge* brCtrlDFGEdge = new DFGEdge(newDFGEdgeID++, left, right);
      // FIXME: Only consider one predecessor for 'phi' node for now.
      //        Need to care about true/false and make proper connection.
      replaceDFGEdges.push_back(replaceDFGEdge);
      newBrDFGEdges.push_back(brDataDFGEdge);
      newBrDFGEdges.push_back(brCtrlDFGEdge);
      break;
    }
  }
  for (DFGEdge* dfgEdge: replaceDFGEdges) {
    m_DFGEdges.remove(dfgEdge);
  }
  for (DFGEdge* dfgEdge: newBrDFGEdges) {
    m_DFGEdges.push_back(dfgEdge);
  }

  connectDFGNodes();
//    DFGEdge* brCtrlDFGEdge = new DFGEdge(m_DFGEdges.size(), left, right);
//    DFGEdge* replaceDFGEdge;
//    for (list<DFGNode*>::iterator predNodeItr=predNodes->begin();
//        predNodeItr!=predNodes->end(); ++predNodeItr) {
//      DFGNode* predNode = *predNodeItr;
//      list<DFGNode*>* visitedNodes = new list<DFGNode*>();
//      // Found one predNode is one the same control/data path as the 'br'.
//      if (searchDFS(left, predNode, visitedNodes)) {
//        replaceDFGEdge = getDFGEdge(predNode, right);
//        DFGEdge* brDataDFGEdge = new DFGEdge(replaceDFGEdge->getID(), predNode, left);
//        m_DFGEdges.remove(replaceDFGEdge);
//        m_DFGEdges.push_back(brDataDFGEdge);
//        break;
//      }
//    }
//    m_DFGEdges.push_back(brCtrlDFGEdge);
//  }
}

void DFG::trimForStandalone() {
  list<DFGNode*> removeNodes;
  for (DFGNode* dfgNode: nodes)
    if (dfgNode->getPredNodes()->size() == 0 and
        dfgNode->getSuccNodes()->size() == 0)
      removeNodes.push_back(dfgNode);

  for (DFGNode* dfgNode: removeNodes)
    nodes.remove(dfgNode);
}

bool DFG::searchDFS(DFGNode* t_target, DFGNode* t_head,
    list<DFGNode*>* t_visitedNodes) {
  for (DFGNode* succNode: *t_head->getSuccNodes()) {
    if (t_target == succNode) {
      return true;
    }
    // succNode is not yet visited.
    if (find(t_visitedNodes->begin(), t_visitedNodes->end(), succNode) ==
          t_visitedNodes->end()) {
      t_visitedNodes->push_back(succNode);
      if (searchDFS(t_target, succNode, t_visitedNodes)) {
        return true;
      }
    }
  }
  return false;
}

// TODO: This is necessary for inter-iteration data dependency
//       checking (ld/st dependency analysis on base address).
void DFG::detectMemDataDependency() {

}

// TODO: Certain opcode can be eliminated, such as bitcast, etc.
void DFG::eliminateOpcode(string t_opcodeName) {

}

