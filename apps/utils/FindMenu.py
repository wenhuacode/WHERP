async def find_menu(data):
    """建树:找爸爸算法
    1万层节点耗时(秒):0.005019187927246094
    """
    # 建立一个 id 对 index 的字典
    res = []
    c_dict = {}
    for index, i in enumerate(data):
        c_dict[i["id"]] = index

    # 用本节点的 parentId 通过字典找到父节点的index
    for i in data:
        if i['parent_id'] == 0:
            res.append(i)
        else:
            papa = data[c_dict[i["parent_id"]]]
            if "children" not in papa.keys():
                papa["children"] = []
            papa["children"].append(i)

    # res = [i for i in data if i["parentId"]==0]s
    return res


async def find_menu_child(data, root):
    """建树:指定找爸爸算法
    1万层节点耗时(秒):0.005019187927246094
    """
    # 建立一个 id 对 index 的字典
    res = []
    c_dict = {}
    for index, i in enumerate(data):
        c_dict[i["id"]] = index

    # 用本节点的 parentId 通过字典找到父节点的index
    for i in data:
        if i['parent_id'] == root:
            res.append(i)
        else:
            papa = data[c_dict[i["parent_id"]]]
            if "children" not in papa.keys():
                papa["children"] = []
            papa["children"].append(i)

    # res = [i for i in data if i["parentId"]==0]s
    return res


async def classifyChild(lists, ids):
    child = []
    datalist = [ids]

    async def find_child(lists, ids):
        for data in lists:
            # 比对节点id
            if data['parent_id'] == ids:
                # 找子节点
                child.append(data)
                # 找子节点id
                child_id = data['id']
                # 递归
                await find_child(lists, child_id)
        return child

    child = await find_child(lists, ids)

    for data in child:
        datalist.append(data['id'])
    return datalist


async def find_child(lists, root):
    # 递归找数据的子节点
    res = []
    c_dict = {}
    for index, i in enumerate(lists):
        c_dict[i["id"]] = index

    for i in lists:
        if i['parent_id'] == root:
            res.append(i)
        else:
            papa = lists[c_dict[i["parent_id"]]]
            if "children" not in papa.keys():
                papa["children"] = []
            papa["children"].append(i)

    return res