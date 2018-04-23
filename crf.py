import codecs
import random


def cut_tag(source, train_output, test_output, index_list):
    # 单字标注
    fin = codecs.open(source, "rb", "utf-8")
    tr_out = codecs.open(train_output, "wb", "utf-8")
    te_out = codecs.open(test_output, "wb", "utf-8")
    i = 0
    for line in fin.readlines():
        new_line = ''
        line = line[:-1]  # 去除\n
        # line = re.sub('/[a-z]+[0-9]*', '', line)  # 去除所有标签
        line = line.split(' ')
        if line == '':
            continue
        else:
            for word in line:
                if '/' not in word:
                    if len(word) == 1:  # 单字词
                        new_line += (word + '\t' + 'S' + '\t' + 'O' + '\n')
                    else:
                        for i in range(len(word)):
                            if i == 0:  # 词首
                                new_line += (word[i] + '\t' + 'B' + '\t' + 'O' + '\n')
                            elif i == len(word) - 1:  # 词尾
                                new_line += (word[i] + '\t' + 'E' + '\t' + 'O' + '\n')
                            else:  # 词中
                                new_line += (word[i] + '\t' + 'M' + '\t' + 'O' + '\n')
                else:
                    w, tag = word.split('/')
                    if len(w) == 1:  # 单字词
                        new_line += (w + '\t' + 'S' + '\t' + 'O' + '\n')
                    else:
                        for i in range(len(w)):
                            if i == 0:  # 词首
                                new_line += (w[i] + '\t' + 'B' + '\t' + 'B' + '\n')
                            elif i == len(w) - 1:  # 词尾
                                new_line += (w[i] + '\t' + 'E' + '\t' + 'I' + '\n')
                            else:  # 词中
                                new_line += (w[i] + '\t' + 'M' + '\t' + 'I' + '\n')
        new_line += '\n'
        if i in index_list:
            tr_out.writelines(new_line)
        else:
            te_out.writelines(new_line)
        i += 1
    fin.close()
    tr_out.close()
    te_out.close()


def select(total_line, index_list):
    for i in range(total_line):
        if random.random() > p:
            index_list.append(i)


def test(s):
    fin = codecs.open(s, "rb", "utf-8")
    list_source = ''
    list_result = ''
    count_source = 0
    count_result = 0
    correct = 0
    wrong = 0
    for line in fin.readlines():
        line = line[:-2]
        if len(line) == 0:
            continue
        list_source += (line.split('\t')[2])
        list_result += (line.split('\t')[3])
    print("extract done!")
    list_source = list_source.split('O')
    list_result = list_result.split('O')
    print("split done!")
    for item in range(list_source.count('')):
        list_source.remove('')
    for item in range(list_result.count('')):
        list_result.remove('')
    print("remove done!")
    length = len(list_source) if len(list_source) < len(list_result) else len(list_result)
    for i in range(length):
        count_source += 1
        count_result += 1
        if list_source[i] == list_result[i]:
            correct += 1
        else:
            wrong += 1
    print(correct, wrong, count_source, count_result)


p = 0.2
total_line = 98558
test("test_result")
# index_list = []
# select(total_line, index_list)
# cut_tag("data_nr.txt", "train_data", "test_data", index_list)
