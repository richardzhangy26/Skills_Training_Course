import json
import os

def extract_steps_to_markdown(json_file_path, output_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        steps_data = data.get('data', [])
        
        markdown_content = []
        
        # Filter for actual script nodes to avoid default start/end nodes if they don't have content
        # or just process all and let the user see. 
        # Usually 'SCRIPT_NODE' contains the content. 
        # Based on the file content, SCRIPT_START and SCRIPT_END have "defaultStepName" and empty prompts.
        # We will filter valid nodes or enumerate all non-empty ones.
        
        script_nodes = [
            step for step in steps_data 
            if step.get('stepDetailDTO', {}).get('nodeType') == 'SCRIPT_NODE'
        ]
        
        # If no SCRIPT_NODE found, fall back to all items (though unlikely based on previous file view)
        if not script_nodes:
             script_nodes = steps_data

        for index, step in enumerate(script_nodes, 1):
            detail = step.get('stepDetailDTO', {})
            
            step_name = detail.get('stepName', '未命名阶段')
            description = detail.get('description', '无描述')
            interactive_rounds = detail.get('interactiveRounds', 0)
            if interactive_rounds is None:
                interactive_rounds = 0
            prologue = detail.get('prologue', '')
            llm_prompt = detail.get('llmPrompt', '')
            
            # Formatting as requested
            step_md = f"### 阶段{index}: {step_name}\n"
            step_md += f"**阶段描述**: {description}  \n"
            step_md += f"**互动轮次**: {interactive_rounds}轮  \n"
            step_md += "**开场白**:  \n"
            step_md += "```\n"
            step_md += f"{prologue}\n"
            step_md += "```  \n"
            step_md += "**提示词**:  \n"
            step_md += "```\n"
            step_md += f"{llm_prompt}\n"
            step_md += "```  \n"
            
            markdown_content.append(step_md)
            
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(markdown_content))
            
        print(f"Successfully extracted {len(script_nodes)} steps to {output_file_path}")
        return True

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Define paths
    # source_json = "/Users/richardzhang/工作/能力训练/skill_training_build/script_step_39d6f69b.json" # User mentioned this path in request but file view showed it in root of work dir?
    # Wait, the prompt says: @/Users/richardzhang/工作/能力训练/script_step_39d6f69b.json
    # But later I viewed it at: /Users/richardzhang/%E5%B7%A5%E4%BD%9C/%E8%83%BD%E5%8A%9B%E8%AE%AD%E7%BB%83/script_step_39d6f69b.json
    # which decoded is /Users/richardzhang/工作/能力训练/script_step_39d6f69b.json
    
    source_json = "/Users/zhangyichi/工作/能力训练/skills_training_course/成都中医药大学-护士人文修养/认知疗方.json"
    output_md = "/Users/zhangyichi/工作/能力训练/skill_training_build/extracted_script.md"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_md), exist_ok=True)
    
    extract_steps_to_markdown(source_json, output_md)
