import os

files = os.listdir('./data/')

image_info = {}
for f in files:
    parts = os.path.splitext(f)[0].split('_')
    if len(parts) <= 2:
        continue
    if parts[0] not in image_info.keys():
        image_info[parts[0]] = {}
    image_info[parts[0]][parts[-2]] = parts[1:-2]
    new_name = "%s_%s_%s.png" % (parts[0], parts[-2], parts[-1])
    os.rename("data/" + f, "data/" + new_name)

for key, attributes in image_info.items():
    with open("./data/%s.txt" % key, "w") as text_file:
        attributes = sorted(attributes.items())
        for value in attributes:
            text_file.write("%s %s\n" % (value[0], value[1][0]))
