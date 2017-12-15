import json, sys, os, fnmatch, argparse, shutil
from collections import OrderedDict


def find_all(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result

def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

def JSON_load(file_name):
    "Load a file which contains the JSON configuration"
    try:
        config = json.loads(open(file_name).read(), object_pairs_hook=OrderedDict)
    except ValueError:
        print("The content of file " + file_name + " does not fit for the JSON standard format. Ignoring...")
        return None
    else:
        return config

def convert(file_name, indentation):
    "Convert a Prompter JSON configuration file to the new schema format"

    config = JSON_load(file_name)

    if config is None:
        return

    if config.get("prompter") is None:
        print("NO PROMPTER CONFIGURATION found for file " + file_name)
        return
    for idx, prmpt in enumerate(config["prompter"]):
        if prmpt["type"] == "local":
            config["voice_data_path"] = config.get('voice_data_path', [])
            # to avoid overwriting
            if prmpt["local"].get("voice_data_path"):
                continue
            found = False
            for data_path in config["voice_data_path"]:
                if data_path.get("vocalizer_path", '') == prmpt["local"]["vocalizer_path"] and prmpt["local"].get("scan_result_storage_path", '') == data_path.get("scan_result_storage_path", ''):
                    found = True
                    break
            if found == False:
                data = {
                    "name": "VE_DATA" + str(idx),
                    "vocalizer_path": prmpt["local"]["vocalizer_path"]
                }
                val = prmpt["local"].get("scan_result_storage_path")
                if val:
                    data["scan_result_storage_path"] = val
                config["voice_data_path"].append(data)

    if config.get("voice_data_path"):
        for prmpt in config["prompter"]:
            if prmpt["type"] == "local" and prmpt["local"].get("voice_data_path") is None:
                # print(json.dumps(prmpt, indent=2))  # for debugging
                for data_path in config["voice_data_path"]:
                    # print(json.dumps(data_path, indent=2))  # for debugging
                    if data_path["vocalizer_path"] == prmpt["local"]["vocalizer_path"] and prmpt["local"].get("scan_result_storage_path", '') == data_path.get("scan_result_storage_path", ''):
                        prmpt["local"]["voice_data_path"] = {"uses": data_path["name"]}
                        prmpt["local"].pop("vocalizer_path", 0)
                        prmpt["local"].pop("scan_result_storage_path", 0)
                        break

    file = open(file_name, 'w')
    dump = json.dumps(config, indent=indentation)
    print >> file, dump
    file.close()

def backup(original_file):
    backup_file = original_file + ".bak"
    shutil.copyfile(original_file, backup_file)
    if os.path.isfile(backup_file):
        print("Backing up file {} to {} success.".format(original_file, backup_file))
    else:
        raise Exception("Backing up file {} to {} failed".format(original_file, backup_file))

def convert_all(file_name, path_info, indent):
    files = find_all(file_name, path_info)
    if not files:
        raise Exception("NO specified file found. Please double check the file name and path info.")
    for file in files:
        print("Converting file " + file)
        backup(file)
        convert(file, indent)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert a Prompter JSON configuration file to the new schema format")
    parser.add_argument("-f", "--file", dest="filename", help="file to be converted, default file name is 'prompterconfig.json'", metavar="FILE", default="prompterconfig.json")
    parser.add_argument("-d", "--dir", dest="pathinfo", help="directory where to search the given file, default dir is the current dir './'", metavar="DIR", default="./")
    parser.add_argument("-i", "--ind", dest="indent", help="an integer for the indentation, default is 4 spaces", metavar="IND", default=4, type=int)
    args = parser.parse_args()

    filename = args.filename
    pathinfo = args.pathinfo
    indent = args.indent

    if filename.split('.')[-1] != "json":
        print("Please convert JSON files only! (*.json)" )
        sys.exit(1)

    print("\nSearching and converting files named '{}' under directory '{}'\n".format(filename, pathinfo))

    try:
        convert_all(filename, pathinfo, indent)
        print("\nDONE - Please diff the file with the original one\n")
    except Exception, e:
        print("\nERROR - {}".format(e.message))

