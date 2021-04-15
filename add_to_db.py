from replit import db

for key in db.keys():
    print(f"{key} : {db[key]}")

id = input("Enter the id of the user : ")
name = input("Enter the real username of the user : ")

db[id] = name