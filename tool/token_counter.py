# token计数器模块
total_tokens = 0

def add_tokens(tokens):
    """累加token数量"""
    global total_tokens
    total_tokens += tokens
    
def get_total_tokens():
    """获取当前累计的token总数"""
    return total_tokens
    
def reset_tokens():
    """重置token计数器"""
    global total_tokens
    total_tokens = 0