import asyncio
import sys
import os

sys.path.append(r'c:\WEB CASE STUDY\antigravity_vscode_ext\backend')
from legion_langgraph_brain import LegionLangGraphAgent
from langchain_core.messages import HumanMessage

async def main():
    agent = LegionLangGraphAgent(provider='nvidia')
    
    # Initialize state
    state = {
        'messages': [HumanMessage(content='Search the registry for system_data_audit_report')],
        'recursion_count': 0,
        'max_recursion_limit': 3
    }
    
    print('Invoking agent...')
    result = await agent.graph.ainvoke(state)
    
    print('\n--- FINAL RESULT ---')
    for m in result['messages']:
        print(m.type, ':', m.content)

if __name__ == '__main__':
    asyncio.run(main())
