import jiphy

def read_file(filepath):
    with open(filepath) as fp:
        content=fp.read()
    return content

def write_file(content, filepath):
    with open(filepath, 'w+', encoding='utf-8') as fp:
        fp.write(content)

def conver_to_py(str, py_path):
    str = str.replace("#duration", "get_event_time_from_now")
    str = str.replace("#ref(", "get_value(attr_list, ")
    str = str.replace("#call_service", "call_service")
    str = str.replace("#raise_event", "raise_event")
    py_str = jiphy.to.python(str)

    line_list = py_str.split("\n")
    #print(line_list)
    new_str = ''
    for line in line_list:
        new_str += ("    " + line + "\n")
    new_str = "from script.script_fun import *\n" + "def script_fun():\n\
    command_list = []\n    attr_list = []\n    event_list = []\n" + new_str + "\
    return command_list, event_list, attr_list"

    new_str = new_str.replace("call_service(", "call_service(command_list, ")
    new_str = new_str.replace("raise_event(", "raise_event(event_list, ")
    write_file(new_str, py_path)

