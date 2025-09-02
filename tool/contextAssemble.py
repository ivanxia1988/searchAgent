#将上下文以更清晰的结构组织起来，让大模型能更好的理解。并且进行部分上下文工程管理，例如添加固定的前缀、后缀等
def assemble_context(system_prompt, task_instruction, history):
    """
    组装结构化的上下文信息
    
    参数:
    system_prompt: 系统提示内容
    task_instruction: 任务说明
    history: 对话历史
    
    返回:
    结构化的上下文字符串
    """
    # 构建结构化的上下文
    structured_context = (
        "[System Prompt]\n"
        f"{system_prompt}\n"
        "\n---\n\n"
        "[Task Instruction]\n"
        f"{task_instruction}\n"
        "\n---\n\n"
        "[Conversation History]\n"
        f"{history}\n"
    )
    
    return structured_context

def assemble_history(step,think,action,obs):
    """
    组装结构化的上下文信息
    
    参数:
    step: 步骤
    think: 思考
    action: 操作内容
    obs: 操作结果
    
    返回:
    结构化的上下文字符串
    """
    # 构建结构化的上下文
    structured_context = (
        f"[第{step}步]\n"
        "[思考过程]\n"
        f"{think}\n"
        "[执行操作]\n"      
        f"{action}\n"
        "[操作结果]\n"
        f"{obs}\n"
        "\n---\n\n"
    )
    
    return structured_context