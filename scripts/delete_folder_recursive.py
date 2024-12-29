import os
import shutil

def delete_folder_recursive(base_path, folder_name):
    for directories in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, directories)):
            if directories == folder_name:
                shutil.rmtree(os.path.join(base_path, directories))
            else:
                delete_folder_recursive(os.path.join(base_path, directories), folder_name)

if __name__ == "__main__":
    
    base_path = input("Enter the base path: ")
    if("~" in base_path):
        base_path = os.path.expanduser("~") + base_path[1:]
    folder_name = input("Enter the folder name to delete: ")
    delete_folder_recursive(os.path.abspath(base_path), folder_name)
    # get absolute path of the folder
    
    
