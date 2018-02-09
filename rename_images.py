from os import listdir, rename

for f in listdir("data"):
    start = 0
    end = 0
    for i in range(len(f)):
        if(f[i] == '_'):
            start = i
            break

    cnt = 0
    for i in range(len(f) - 1, 0, -1):
        if(f[i] == '_'):
            end = i
            cnt += 1
        if cnt == 2:
            break
    new_name = f[:start] + f[end:]
    rename("data/" + f, "data/" + new_name)
