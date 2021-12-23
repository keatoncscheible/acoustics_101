import re

signal_slot_connection_bug_regex = re.compile(r'\[\'([a-zA-Z0-9_]+)\'\]\.connect\(')
deprecated_qstring_regex = re.compile(r'(QString)')

fixed_ui_file = ''
with open('pa_methods_ui.py', "r") as file:
    for line in file:

        result = signal_slot_connection_bug_regex.search(line)
        if result is not None:
            line = line.replace("'{}'".format(result.group(1)), result.group(1))

        result = deprecated_qstring_regex.search(line)
        if result is not None:
            line = line.replace(result.group(1), 'str')

        fixed_ui_file += line
            
with open('pa_methods_ui.py', "w") as file:
    file.write(fixed_ui_file)