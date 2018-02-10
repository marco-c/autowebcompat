import os

files = os.listdir('./data/')

image_info = {}
for f in files:
    parts = os.path.splitext(f)[0].split('_')
    if len(parts) <= 2:
        continue
    webcompat_id = parts[0]
    sequence_no = parts[-2]
    elem_id = '_'.join(parts[1:-2])
    browser = parts[-1]
    if webcompat_id not in image_info.keys():
        image_info[webcompat_id] = {}
    image_info[webcompat_id][sequence_no] = elem_id
    new_name = "%s_%s_%s.png" % (webcompat_id, sequence_no, browser)
    os.rename("data/" + f, "data/" + new_name)

for webcompat_id, seq_no_and_elem_id in image_info.items():
    with open("./data/%s.txt" % webcompat_id, "w") as text_file:
        seq_no_and_elem_id = sorted(seq_no_and_elem_id.items())
        for value in seq_no_and_elem_id:
            sequence_no = value[0]
            elem_id = value[1]
            text_file.write("{\"id\" : \"%s\"}\n" % (elem_id))
