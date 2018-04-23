import codecs
import re
import json
import numpy as np


def save_as_file(obj, output):
    # 以json文件形式存储结果
    with open(output, "w") as out:
        json.dump(obj, out, indent=4, ensure_ascii=False, sort_keys=False)
    out.close()


def get_pos_dict(source, output=None):
    # 获取pos_dict
    fin = codecs.open(source, "rb", "utf-8")
    i = 0
    for line in fin.readlines():
        result = re.findall('/[a-z]+[0-9]*', line)  # 用正则表达式找到所有pos
        for p in result:
            p = p[1:]  # 去除'/'
            if p not in pos_dict:
                pos_dict[p] = i
                i += 1
    fin.close()
    if output is not None:
        save_as_file(pos_dict, output)


def get_char_dict(source, output=None):
    # 获取char_dict
    fin = codecs.open(source, "rb", "utf-8")
    count = 0
    for line in fin.readlines():
        line = line[:-1]  # 去除\n
        line = re.sub(' ', '', line)  # 去除空格
        for item in line:  # 不在char_dict中则加入
            if item not in char_dict:
                char_dict[item] = count
                count += 1
    if output is not None:
        save_as_file(char_dict, output)


def get_word_dict(source, output=None):
    # 补充char_dict
    fin = codecs.open(source, "rb", "utf-8")
    count = 0
    for line in fin.readlines():
        line = line[:-1]  # 去除\n
        line = line.split(' ')
        for item in line:  # 不在word_dict中则加入
            if item not in char_dict:
                char_dict[item] = count
                count += 1
    if output is not None:
        save_as_file(char_dict, output)


def cut_tag(source, output):
    # 单字标注
    fin = codecs.open(source, "rb", "utf-8")
    out = codecs.open(output, "wb", "utf-8")
    for line in fin.readlines():
        new_line = ''
        line = line[:-1]  # 去除\n
        line = re.sub('/[a-z]+[0-9]*', '', line)  # 去除所有标签
        line = line.split(' ')
        if line == '':
            continue
        else:
            for word in line:
                if len(word) == 1:  # 单字词
                    new_line += (word + '/S ')
                else:
                    for i in range(len(word)):
                        if i == 0:  # 词首
                            new_line += (word[i] + '/B ')
                        elif i == len(word) - 1:  # 词尾
                            new_line += (word[i] + '/E ')
                        else:  # 词中
                            new_line += (word[i] + '/M ')
        new_line += '\n'
        out.writelines(new_line)
    fin.close()
    out.close()


def remove_tags(source, output, action=0):
	# 从raw_data.txt中去除tags
    fin = codecs.open(source, "rb", "utf-8")
    out = codecs.open(output, "wb", "utf-8")
    for line in fin.readlines():
        line = line[:-1]  # 去除\n
        line = re.sub('/[a-z]+[0-9]*', '', line)  # 去除标注
        if action == 1:
            line = re.sub(' ', '', line)
        line += '\n'  # 添加\n
        out.writelines(line)
    fin.close()
    out.close()


def hmm(source, c_dict, t_dict, begin, end, mat_a, mat_b, vec_p):
    fin = codecs.open(source, "rb", "utf-8")
    pr_tag_id = -1
    count_line = 0
    for line in fin.readlines():
        count_line += 1
        if begin > count_line or count_line > end:
            line = line[:-1]  # 去除\n
            line = line.split(' ')
            if line != "":
                for ch in line:
                    if ch == '':
                        continue
                    else:
                        c = ch.split('/')
                        char = c[0] if c[0] != '' else '/'  # 如果是'/'字符会和标注'/'冲突
                        tag = c[-1]
                        try:
                            char_id = c_dict[char]  # 获得字符编号
                            tag_id = t_dict[tag]  # 获得标签编号
                            mat_b[char_id, tag_id] += 1
                            vec_p[tag_id] += 1
                            if pr_tag_id != -1:
                                mat_a[pr_tag_id, tag_id] += 1
                            pr_tag_id = tag_id
                        except KeyError:
                            continue
                pr_tag_id = -1
    tag_num = len(t_dict)
    for i in range(tag_num):
        s = sum(mat_a[i])
        for j in range(tag_num):
            mat_a[i][j] /= s
    for i in range(tag_num):  # 加1平滑
        s = sum(mat_b[i]) + tag_num
        for j in range(tag_num):
            mat_b[i][j] = (mat_b[i][j] + 1) / s
    for i in range(tag_num):
        s = sum(vec_p)
        for j in range(tag_num):
            vec_p[j] /= s
    fin.close()
    return mat_a, mat_b, vec_p


def viterbi(sentence, c_dict, t_dict, vec_p, mat_a, mat_b, action):
    v = [{}]
    path = {}
    states = []
    for key in t_dict.keys():
        states.append(key)
    states = tuple(states)
    for y in states:   # 初始值
        v[0][y] = vec_p[t_dict[y]] * mat_b[c_dict[sentence[0]]][t_dict[y]]   # 在位置0，以y状态为末尾的状态序列的最大概率
        path[y] = [y]
    if action != 0:
        sentence = sentence.split(' ')
    for t in range(1, len(sentence)):
        v.append({})
        newpath = {}
        for y in states:      # 从y0 -> y状态的递归
            (prob, state) = max([(v[t - 1][y0] * mat_a[t_dict[y0]][t_dict[y]] * mat_b[c_dict[sentence[t]]][t_dict[y]],
                                  y0) for y0 in states])
            v[t][y] = prob
            newpath[y] = path[state] + [y]
        path = newpath  # 记录状态序列
    (prob, state) = max([(v[len(sentence) - 1][y], y) for y in states])  # 在最后一个位置，以y状态为末尾的状态序列的最大概率
    return prob, path[state]  # 返回概率和状态序列


def cut(c_dict, t_dict, vec_p, mat_a, mat_b, begin, end, source, output, action=0):
    fin = codecs.open(source, "rb", "utf-8")
    fout = codecs.open(output, "wb", "utf-8")
    count_line = 0
    for line in fin.readlines():
        count_line += 1
        if begin <= count_line <= end or begin == end:
            line = line[:-1]  # 去除'\n'
            if action == 0:  # 分词
                line = re.sub(' ', '', line)  # 去除空格
            prob, path = viterbi(line, c_dict, t_dict, vec_p, mat_a, mat_b, action)
            if action != 0:  # 词性标注
                line = line.split(' ')
            new_line = ''
            for i in range(len(line)):
                if path[i] == 'S' or path[i] == 'E':
                    new_line += (line[i] + ' ')
                elif path[i] != 'B' and path[i] != 'M':
                    new_line += (line[i] + '/' + path[i] + ' ')
                else:
                    new_line += line[i]
            if new_line[-1] == ' ':
                new_line = new_line[:-1] + '\n'
            else:
                new_line += '\n'
            print(new_line)
            fout.writelines(new_line)
    fin.close()
    fout.close()


def compare(begin, end, source, result):
    fin = codecs.open(source, "rb", "utf-8")
    fre = codecs.open(result, "rb", "utf-8")
    count_line = 0
    correct = 0
    total = 0
    for line in fin.readlines():
        count_line += 1
        if begin <= count_line <= end:
            line = line[:-1]
            line_re = fre.readline()
            line_re = line_re[:-1]
            line = line.split(' ')
            line_re = line_re.split(' ')
            count_ch_1 = 0
            i = 0
            j = 0
            count_ch_2 = 0
            while i < len(line) - 1 and j < len(line_re) - 1:
                len_i = len(line[i].split('/')[0])
                len_j = len(line_re[j].split('/')[0])
                if count_ch_1 == count_ch_2:
                    count_ch_1 += len_i
                    count_ch_2 += len_j
                    i += 1
                    j += 1
                    total += 1
                elif count_ch_1 > count_ch_2:
                    count_ch_2 += len_j
                    j += 1
                    total += 1
                else:
                    count_ch_1 += len_i
                    i += 1
                if count_ch_1 == count_ch_2 and len_i == len_j:
                    if line[i] == line_re[j]:
                        correct += 1
    fout=codecs.open("accuracy.txt", "a", "utf-8")
    fout.write(str(correct/total), '\n')


def test(output_cut, output_part, begin, end):
    global char_dict
    char_dict = {}
    get_char_dict("raw.txt")
    A = np.zeros([len(tag_dict), len(tag_dict)])
    B = np.zeros([len(char_dict), len(tag_dict)])
    pi = np.zeros([len(tag_dict)])
    A, B, pi = hmm('cut_tag_data.txt', char_dict, tag_dict, begin, end, A, B, pi)
    cut(char_dict, tag_dict, pi, A, B, begin, end, "raw.txt", output_cut)

    get_word_dict("no_tags_data.txt")
    get_word_dict(output_cut)
    A = np.zeros([len(pos_dict), len(pos_dict)])
    B = np.zeros([len(char_dict), len(pos_dict)])
    pi = np.zeros([len(pos_dict)])
    A, B, pi = hmm('raw_data.txt', char_dict, pos_dict, begin, end, A, B, pi)
    cut(char_dict, pos_dict, pi, A, B, 0, 0, output_cut, output_part, 1)
    compare(begin, end, "raw_data.txt", output_part)


remove_tags("raw_data.txt", "no_tags_data.txt")
remove_tags("raw_data.txt", "raw.txt", 1)
word_dict = {}
pos_dict = {}
tag_dict = {'B': 0, 'M': 1, 'E': 2, 'S': 3}
get_pos_dict("raw_data.txt")
total_lines = 98558
t = total_lines // 5
cut_tag("raw_data.txt", "cut_tag_data.txt")
char_dict = {}
# test("cut_result_0.txt", "part_result_0.txt", t * 4 + 1, total_lines)
# test("cut_result_1.txt", "part_result_1.txt", 0, t)
test("cut_result_2.txt", "part_result_2.txt", t + 1, t * 2)
test("cut_result_3.txt", "part_result_3.txt", t * 2 + 1, t * 3)
test("cut_result_4.txt", "part_result_4.txt", t * 3 + 1, t * 4)


