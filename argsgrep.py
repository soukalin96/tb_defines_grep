# argsgrep.py
import argparse
import re
import csv
import os

# Define the command line arguments
parser = argparse.ArgumentParser(description='Parse and sort defines and plusargs from all .v/.sv/.svh flies in a directory/subdirs')
parser.add_argument('-d', '--directory', help='The directory to search recursively', default='./')
parser.add_argument('-o', '--output', help='The output CSV file name. Default : output.csv', default='output.csv')
parser.add_argument('-i', '--input', help='The input CSV file name containing strings to dematch. Default : input.csv', default='input.csv')
parser.add_argument('--defs', action='store_true', help='Adds `defines to csv')
args = parser.parse_args()

# Define the regex patterns for defines and plusargs
plusarg_pattern = re.compile(r'\$(test|value)\$plusargs\(\s*"([^"]+)"')
if_define_pattern = re.compile(r'\`(ifdef|ifndef|elsif)\s+(\w*)')
define_pattern = re.compile(r'\`(define)\s(.*?\(.*?\)|.*?.*?\)|\S+)(.*)')

# Create empty lists to store the defines and plusargs
plusargs = []
cmd_defines = []
tb_defines = []
all_args = []
temp_tb = []

# get TB defines match str
file = open(args.input, "r") #need to auto populate input.csv
data = list(csv.DictReader(file, delimiter=","))
file.close()    

ip_tb_defines_match = [str(row["TB defines"]) for row in data]
ip_netlist_defines_match = [str(row["Netlist defines"]) for row in data]
ip_tb_defines_match = list(filter(None, ip_tb_defines_match))
ip_netlist_defines_match = list(filter(None, ip_netlist_defines_match))

# assign directory
directory = args.directory
for subdir, dirs, files in os.walk(directory):
    for file in files:
        extentions = (".v", ".sv", ".svh")
        if file.endswith(extentions):
            
            # Open the Verilog file and read its contents
            with open((os.path.join(subdir, file)), 'r') as sv_file:
                verilog = sv_file.read()

                # Loop through each line of the Verilog file
                for line in verilog.splitlines():
                    
                    # Match the plusarg pattern
                    plusarg_match = plusarg_pattern.search(line)
                    if plusarg_match:
                        type = plusarg_match.group(1)
                        if (type=="value"):
                            name = plusarg_match.group(2)
                            # Split the format string by '=' to get the name and type of the plusarg
                            name, loader = name.split('=')
                        if (type=="test"):
                            name = plusarg_match.group(2)
                        # Add the plusarg to the list as a tuple of (name, type, 'plusarg') 
                        plusargs.append((name, type, 'Plusarg'))
                        plusargs = list(dict.fromkeys(plusargs))
                        
                    # Match the ifdef/ifndef pattern  
                    cmd_defines_match = if_define_pattern.search(line)
                    if cmd_defines_match:
                        type = cmd_defines_match.group(1)
                        name = cmd_defines_match.group(2)
                        # Add the define to the list as a tuple of (name, type, 'identifier') 
                        if any(substring in name for substring in ip_tb_defines_match) or any(substring in name for substring in ip_netlist_defines_match): #need logic to determine TB defines or hardcode
                            cmd_defines.append((name, '+def', 'TB defines'))
                        else :
                            cmd_defines.append((name, '+def', 'CMD_LINE defines'))
                        cmd_defines = list(dict.fromkeys(cmd_defines))
                        
                    # Match the define pattern  
                    tb_defines_match = define_pattern.search(line)
                    if tb_defines_match:
                        type = tb_defines_match.group(1)
                        name = tb_defines_match.group(2)
                        def_type = tb_defines_match.group(3)
                        # Add the define to the list as a tuple of (name, type, 'type')
                        if def_type:
                            if def_type.find('.') != -1:
                                tb_defines.append((name, type, 'HIER'))
                            elif name.find('(') != -1:
                                tb_defines.append((name, type, 'Macro'))
                            else:
                                tb_defines.append((name, type, 'TB defines'))
                        else :
                            tb_defines.append((name, type, 'TB defines (no args)'))    
                        tb_defines = list(dict.fromkeys(tb_defines)) 
                        
# Sort the defines and plusargs by name
if args.defs :
    all_args = plusargs + cmd_defines + tb_defines
else : 
    all_args = plusargs + cmd_defines
all_args.sort(key=lambda x: x[2])

# Open the output CSV file and write the header row
with open(args.output, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['Name', 'Type', 'Kind'])

    # Write the defines and plusargs to the CSV file
    for item in all_args:
        writer.writerow(item)
