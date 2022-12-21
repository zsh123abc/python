from xml.dom import minidom


def create_xml_minidom(save_name):
    # 新建 xml 文档对象
    doc = minidom.Document()

    # 创建根节点
    root = doc.createElement('根节点')
    # 设置根节点属性
    root.setAttribute('csdn', 'https://blog.csdn.net/qq_42951560')
    # 添加根节点到文档对象
    doc.appendChild(root)

    # 创建注释节点
    comment = doc.createComment("Xavier's Profile")
    root.appendChild(comment)

    # 创建文本节点
    text = doc.createTextNode('文本节点')
    root.appendChild(text)

    # 创建第一个叶子节点
    name = doc.createElement('叶子节点name')
    name.appendChild(doc.createTextNode('叶子节点的数据'))
    root.appendChild(name)

    # 创建第二个叶子节点
    friends = doc.createElement('叶子节点firends')
    friends_list = [
        {'name': 'Jack', 'age': 18, 'gender': 'male'},
        {'name': 'John', 'age': 19, 'gender': 'male'},
        {'name': 'jane', 'age': 20, 'gender': 'female'}
    ]
    for item in friends_list:
        friend = doc.createElement('叶子节点子节点friend')
        name = doc.createElement('叶子节点子节点子节点name')
        name.appendChild(doc.createTextNode(item['name']))
        age = doc.createElement('age')
        age.appendChild(doc.createTextNode(str(item['age'])))
        gender = doc.createElement('gender')
        gender.appendChild(doc.createTextNode(item['gender']))
        friend.appendChild(name)
        friend.appendChild(age)
        friend.appendChild(gender)
        friends.appendChild(friend)
    root.appendChild(friends)

    # 保存 xml 文档对象
    with open(save_name, 'wb') as f:
        f.write(doc.toprettyxml(encoding='utf-8'))


if __name__ == '__main__':
    create_xml_minidom('xmltext.xml')
