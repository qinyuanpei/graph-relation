import os, sys
import jieba, codecs, math
import jieba.posseg as pseg
from pyecharts import options as opts
from pyecharts.charts import Graph

class RelationExtractor:

	def __init__(self, fpStopWords, fpNameDicts, fpAliasNames):
		# 人名词典
		self.name_dicts = [line.strip().split(' ')[0] for line in open(fpNameDicts,'rt',encoding='utf-8').readlines()]
		# 停止词表
		self.stop_words = [line.strip() for line in open(fpStopWords,'rt',encoding='utf-8').readlines()]
		# 别名词典
		self.alias_names = dict([(line.split(',')[0].strip(), line.split(',')[1].strip()) for line in open(fpAliasNames,'rt',encoding='utf-8').readlines()])
		# 加载词典
		jieba.load_userdict(fpNameDicts)

	def extract(self, fpText):
		# 人物关系
		relationships = {}
		# 人名频次
		name_frequency = {}
		# 每个段落中的人名
		name_in_paragraph = []

        # 读取小说文本，统计人名出现的频次，以及每个段落中出现的人名
		with codecs.open(fpText, "r", "utf8") as f:
			for line in f.readlines():
				poss = pseg.cut(line)
				name_in_paragraph.append([])
				for w in poss:
					if w.flag != "nr" or len(w.word) < 2:
						continue
					if (w.word in self.stop_words):
						continue
					if (not w.word in self.name_dicts and w.word != '半泽'):
						continue
					# 规范化人物姓名，例：半泽->半泽直树，大和田->大和田晓
					word = w.word
					if (self.alias_names.get(word)):
						word = self.alias_names.get(word)  
					name_in_paragraph[-1].append(word)
					if name_frequency.get(word) is None:
						name_frequency[word] = 0
						relationships[word] = {}
					name_frequency[word] += 1

		# 基于共现组织人物关系
		for paragraph in name_in_paragraph:
			for name1 in paragraph:
				for name2 in paragraph:
					if name1 == name2:
						continue
					if relationships[name1].get(name2) is None:
						relationships[name1][name2] = 1
					else:
						relationships[name1][name2] = relationships[name1][name2] + 1
        
		# 返回节点和边
		return name_frequency, relationships

	def exportGephi(self, nodes, relationships):
		# 输出节点
		with codecs.open("./output/node.txt", "w", "gbk") as f:
			f.write("Id Label Weight\r\n")
			for name, freq in nodes.items():
				f.write(name + " " + name + " " + str(freq) + "\r\n")
		# 输出边
		with codecs.open("./output/edge.txt", "w", "gbk") as f:
			f.write("Source Target Weight\r\n")
			for name, edges in relationships.items():
				for v, w in edges.items():
					if w > 0:
						f.write(name + " " + v + " " + str(w) + "\r\n")   

	def exportECharts(self, nodes, relationships):
		# 总频次，用于数据的归一化
		total = sum(list(map(lambda x:x[1], nodes.items())))

		# 输出节点
		nodes_data = []
		for name, freq in nodes.items():
			nodes_data.append(opts.GraphNode(
				name = name, 
				symbol_size = round(freq / total * 100, 2), 
				value = freq,
			)),

		# 输出边
		links_data = []
		for name, edges in relationships.items():
				for v, w in edges.items():
					if w > 0:
						links_data.append(opts.GraphLink(source = v, target = w, value = w))

		# 绘制Graph
		c = (
			Graph()
			.add(
				"",
				nodes_data,
				links_data,
				gravity = 0.2,
				repulsion = 8000,
				is_draggable = True,
				symbol = 'circle',
				linestyle_opts = opts.LineStyleOpts(
					curve = 0.3, width = 0.5, opacity = 0.7
				),
				edge_label = opts.LabelOpts(
					is_show = False, position = "middle", formatter = "{b}->{c}"
				),
			)
			.set_global_opts(
				title_opts = opts.TitleOpts(title="半泽直树原著小说人物关系抽取")
			)
			.render("./docs/半泽直树原著小说人物关系抽取.html")
		)


if (__name__ == '__main__'):
	extractor = RelationExtractor(
		'./input/停用词词典.txt',
		'./input/人名词典.txt',
		'./input/别名词典.txt'
	)
	nodes, relationships = extractor.extract('./input/半泽直树.txt')
	extractor.exportGephi(nodes, relationships)
	extractor.exportECharts(nodes, relationships)