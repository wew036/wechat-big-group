#!/usr/bin/env python3
# coding:utf-8

# Copyright (c) 2018, Zhaoyang Su
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# 使用前提
# 1. 有可以24小时一直运行的能联网的电脑（Windows, Mac, 或者Linux）
# 2. 有可以登录网页版微信的账号（新建的账号无此功能）
# 3. 不介意所有转发的消息从另一个群看起来都是从你这个微信账号上发出的
# 4. 使用后，该微信账号不能再在其他电脑使用桌面终端或者网页版微信（一使用，本程序就会退出，
#    那时将需要重新启动
# 5. 微信网页版会每过几周会自动退出。需要定期检查并且重新启动本程序

# 安装方法
# 1. 安装 python 3.x 和 pip 3.x
# 2. 安装 itchat
#    pip install itchat
# 3. 如果你使用Windows, 去掉下面代码中第一个auto_login那一行的注释，并且注释掉第二个auto_login那一行
# 4. 把所有需要互转的群保存到微信的通讯录。
# 5. 运行本程序
#    python wechat.py

import sys

import itchat
import time
import re
import os
from itchat.content import *


# {msg_id:{forward_msgs:[{chatroom:{}, mgs:{}},{}]}, msg_data:{}, msg_time}
msg_dict = {}

# 自动回复文本等类别的群聊消息
# isGroupChat=True表示为群聊消息
@itchat.msg_register([TEXT, SHARING], isGroupChat=True)
def group_reply_text(msg):
	clean_msg_cache()
	if re.search(r"##no-forward##", msg['Content']) is not None:
		return

	# 消息来自于哪个群聊
	chatroom_id = msg['FromUserName']
	self_id = msg['User']['Self']['UserName']
	is_self = False;
	if chatroom_id == self_id:
		chatroom_id = msg['ToUserName']
		is_self = True

	ts = time.time()
	msg_id = msg["MsgId"]
	msg_dict.update({msg_id: {"forward_msgs":[], "msg_data": msg, "msg_time": ts}});

	print("=============================================")
	print(chatroom_ids)
	print(chatroom_id)
#	print(msg)
	print("=============================================")
	# 消息并不是来自于需要同步的群
	if not chatroom_id in chatroom_ids:
		return

	# 发送者的昵称
	username = msg['ActualNickName']

	#获取群名
	group_name = chatroom_info.get(chatroom_id)

	if msg['Type'] == TEXT:
		content = msg['Content']
	elif msg['Type'] == SHARING:
		content = msg['Text']

	# 根据消息类型转发至其他需要同步消息的群聊
	if msg['Type'] == TEXT:
		for item in chatrooms:
			if not item['UserName'] == chatroom_id:
				msg_new = {}
				if is_self:
					msg_new = itchat.send(msg['Content'], item['UserName'])
				else:
					msg_new = itchat.send('%s—%s 说:\n%s' % (group_name, username, msg['Content']), item['UserName'])
				msg_dict.get(msg_id).get("forward_msgs").append({"chatroom": item, "msg":msg_new})
	elif msg['Type'] == SHARING:
		for item in chatrooms:
			if not item['UserName'] == chatroom_id:
				msg_new = {}
				if is_self:
					msg_new = itchat.send('%s\n%s' % (msg['Text'], msg['Url']), item['UserName'])
				else:
					msg_new = itchat.send('%s-%s 分享：\n%s\n%s' % (group_name, username, msg['Text'], msg['Url']), item['UserName'])
				msg_dict.get(msg_id).get("forward_msgs").append({"chatroom": item, "msg":msg_new})


# 自动回复图片等类别的群聊消息
# isGroupChat=True表示为群聊消息
@itchat.msg_register([PICTURE, ATTACHMENT, VIDEO], isGroupChat=True)
def group_reply_media(msg):
	clean_msg_cache()
	# 消息来自于哪个群聊
	chatroom_id = msg['FromUserName']
	self_id = msg['User']['Self']['UserName']
	is_self = False;
	if chatroom_id == self_id:
		chatroom_id = msg['ToUserName']
		is_self = True

	ts = time.time()
	msg_id = msg["MsgId"]
	msg_dict.update({msg_id: {"forward_msgs":[], "msg_data": msg, "msg_time": ts}});

	# 发送者的昵称
	username = msg['ActualNickName']

	# 消息并不是来自于需要同步的群
	if not chatroom_id in chatroom_ids:
		return

	#获取群名
	group_name = chatroom_info.get(chatroom_id)
	# 如果为gif图片则不转发
#	if msg['FileName'][-4:] == '.gif':
#		return

	# 下载图片等文件
	msg['Text'](msg['FileName'])
	# 转发至其他需要同步消息的群聊
	for item in chatrooms:
		if not item['UserName'] == chatroom_id:
			statinfo = os.stat(msg['FileName'])
			if statinfo.st_size != 0:
				msg_new = itchat.send('以下图片源自 %s—%s' % (group_name, username), item['UserName'])
				msg_new = itchat.send('@%s@%s' % ({'Picture': 'img', 'Video': 'vid'}.get(msg['Type'], 'fil'), msg['FileName']), item['UserName'])
				msg_dict.get(msg_id).get("forward_msgs").append({"chatroom": item, "msg":msg_new})

# 注册消息撤回回调
@itchat.msg_register([NOTE], isGroupChat=True)
def send_msg_helper(msg):
	clean_msg_cache()
	if re.search(r"type=\"revokemsg\"", msg['Content']) is not None:
		# 获取消息的id
		old_msg_id = re.search("\<msgid\>(.*?)\<\/msgid\>", msg['Content']).group(1)
		data = msg_dict.get(old_msg_id, None)
		if data:
			forward_msgs = data.get("forward_msgs")
			for item in forward_msgs:
				chatroom = item["chatroom"]
				recall_msg_id = item["msg"]["MsgID"]
				itchat.revoke(recall_msg_id, chatroom['UserName'])
			# 删除字典旧消息
			msg_dict.pop(old_msg_id)

def clean_msg_cache():
	ts_now = time.time()
	keys = list()
	for key in msg_dict.keys():
		if msg_dict[key]["msg_time"] < ts_now - 180 :
			keys.append(key)

	for key in keys:
		msg_dict.pop(key)
	return

# 扫二维码图像登录（适合用于Windows）
#itchat.auto_login(hotReload=False)

# 在文本终端显示二维码（必须用黑底白字）
itchat.auto_login(hotReload=True, enableCmdQR=2)

# 获取所有通讯录中的群聊
# 需要在微信中将需要同步的群聊都保存至通讯录
chatrooms = itchat.get_chatrooms(update=True, contactOnly=True)
chatroom_ids = [c['UserName'] for c in chatrooms]
chatroom_info = {}
for item in chatrooms:
	chatroom_info[str(item['UserName'])] = item["PYQuanPin"]


print('正在监测的群聊：', len(chatrooms), '个')
print("===================================")
print(chatroom_ids)
print("===================================")
## 开始监测
itchat.run()
