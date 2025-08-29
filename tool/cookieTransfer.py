#该方法用于将插件下载的cookie格式调整成playwright可以使用的格式
def format_cookie(cookie):
    for cook in cookie:
        if cook["sameSite"] == "lax" or cook["sameSite"] == "unspecified":
            cook["sameSite"] = "Lax"
        elif cook["sameSite"] == "no_restriction":
            cook["sameSite"] = "None"
    return cookie