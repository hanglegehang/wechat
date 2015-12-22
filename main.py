# -*- coding: utf-8 -*-
# @Date    : 2014-06-28 13:16:23
# @Author  : xindervella@gamil.com yml_bright@163.com

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from mod.models.db import engine
from mod.user.user_handler import UserHandler
from mod.units.curriculum_handler import CurriculumHandler
from mod.units.renew_handler import RenewHandler
from mod.units.gpa_handler import GPAHandler
from mod.units.srtp_handler import SRTPHandler
from mod.units.update_handler import UpdateHandler
from mod.units.card_handler import CradHandler
from mod.units import update
from mod.units import get
from mod.units import play
from mod.units import quanyi
from mod.models.user import User
from mod.units.weekday import today, tomorrow
from mod.units.config import LOCAL
from mod.units.ticket_handler import ticket_handler
from mod.units.yuyue_handler import yuyueHandler
import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import tornado.gen
import wechat
import os, sys
from time import localtime, strftime, time

from tornado.options import define, options
define('port', default=7200, help='run on the given port', type=int)


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/wechat2/', WechatHandler),
            (r'/wechat2/register/([\S]+)', UserHandler),
            (r'/wechat2/curriculum/([\S]+)', CurriculumHandler),
            (r'/wechat2/renew/([\S]+)/([\S]+)', RenewHandler),
            (r'/wechat2/gpa/([\S]+)', GPAHandler),
            (r'/wechat2/card/([\S]+)', CradHandler),
            (r'/wechat2/srtp/([\S]+)', SRTPHandler),
            (r'/wechat2/update/([\S]+)/([\S]+)', UpdateHandler),
            (r'/wechat2/yuyue/([\S]+)',yuyueHandler),

        ]
        settings = dict(
            cookie_secret="7CA71A57B571B5AEAC5E64C6042415DE",
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
            debug=True
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = scoped_session(sessionmaker(bind=engine,
                                              autocommit=False, autoflush=True,
                                              expire_on_commit=False))


class WechatHandler(tornado.web.RequestHandler):

    @property
    def db(self):
        return self.application.db

    @property
    def unitsmap(self):
        return {
            'update-curriculum': self.update_curriculum,
            'today-curriculum': self.today_curriculum,
            'tomorrow-curriculum': self.tomorrow_curriculum,
            'new-curriculum': self.new_curriculum,
            'pe': self.pe_counts,
            'library': self.rendered,
            'gpa': self.gpa,
            'update-gpa': self.update_gpa,
            'srtp': self.srtp,
            'update-srtp': self.update_srtp,
            'play': self.play,
            'change-user': self.change_user,
            'help': self.help,
            'nic': self.nic,
            'card': self.card,
            'lecture': self.lecture,
            'lecturenotice': self.lecturenotice,
            'jwc': self.jwc,
            'searchlib': self.searchlib,
            'schoolbus': self.schoolbus,
            'quanyi': self.quanyi_info,
            'phylab': self.phylab,
            'grade': self.grade,
            'ticket': self.ticket,
            'dm':self.dm,
            'room':self.room,
            'yuyue':self.yuyue,
            'xiaoli':self.xiaoli,
            'exam':self.exam,
            'feedback':self.feedback,
            'tice':self.tice,
            'nothing': self.nothing
        }

    def on_finish(self):
        self.db.close()

    def get(self):
        self.wx = wechat.Message(token='LiangJ')
        if self.wx.check_signature(self.get_argument('signature', default=''),
                                   self.get_argument('timestamp', default=''),
                                   self.get_argument('nonce', default='')):
            self.write(self.get_argument('echostr'))
        else:
            self.write('access verification fail')

    @tornado.web.asynchronous
    def post(self):
        self.wx = wechat.Message(token='LiangJ')
        s = self.wx.check_signature(self.get_argument('signature', default=''),
                                   self.get_argument('timestamp', default=''),
                                   self.get_argument('nonce', default=''))
        # with open("/var/tmp/t",'w+') as f:
        #     f.write(s+'\n\n')
        if self.wx.check_signature(self.get_argument('signature', default=''),
                                   self.get_argument('timestamp', default=''),
                                   self.get_argument('nonce', default='')):
            self.wx.parse_msg(self.request.body)
            try:
                typelog = "log"
                if self.wx.msg_type == 'event' and self.wx.event == 'subscribe':
                    self.write(self.wx.response_text_msg('welcome'))
                    self.finish()
                elif self.wx.msg_type == 'text':
                    try:
                        user = self.db.query(User).filter(
                            User.openid == self.wx.openid).one()
                        if user.state == 0:
                            self.unitsmap[self.wx.content_key(self.wx.content)](user)
                        elif user.state == 1:
                            self.simsimi(self.wx.raw_content, user)
                    except NoResultFound:
                        self.write(self.wx.response_text_msg(
                            u'<a href="%s/register/%s">=。= 不如先点我绑定一下？</a>' % (
                                LOCAL, self.wx.openid)))
                        self.finish()
                elif self.wx.msg_type == 'event':
                    try:
                        typelog = self.wx.event_key
                        user = self.db.query(User).filter(
                            User.openid == self.wx.openid).one()
                        try:
                            self.unitsmap[self.wx.event_key](user)
                        except KeyError:
                            self.finish()
                    except NoResultFound:
                        self.write(self.wx.response_text_msg(
                            u'<a href="%s/register/%s">=。= 不如先点我绑定一下？</a>' % (
                                LOCAL, self.wx.openid)))
                        self.finish()
                elif self.wx.msg_type == 'voice':
                    try:
                        user = self.db.query(User).filter(
                            User.openid == self.wx.openid).one()
                        if user.state == 0:
                            self.unitsmap[self.wx.content_key(self.wx.voice_content)](user)
                        elif user.state == 1:
                            self.simsimi(self.wx.voice_content, user)
                    except NoResultFound:
                        self.write(self.wx.response_text_msg(
                            u'<a href="%s/register/%s">=。= 不如先点我绑定一下？</a>' % (
                                LOCAL, self.wx.openid)))
                        self.finish()
                else:
                    self.write(self.wx.response_text_msg(u'??'))
                    self.finish()
            except:
                with open('wechat_error.log','a+') as f:
                    f.write(strftime('%Y%m%d %H:%M:%S in [wechat]', localtime(time()))+'\n'+str(sys.exc_info()[0])+'\n'+typelog+'\n'+str(sys.exc_info()[1])+'\n\n')
                self.write(self.wx.response_text_msg(u'小猴正在自我改良中～稍候再试， 么么哒！'))
                self.finish()
        else:
            self.write('message processing fail')
            self.finish()

    # 课表
    # 更新频率较低，无需缓存

    def update_curriculum(self, user):
        msg = update.curriculum(self.db, user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def today_curriculum(self, user):
        msg = get.curriculum(self.db, user, today())
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def tomorrow_curriculum(self, user):
        msg = get.curriculum(self.db, user, tomorrow())
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def new_curriculum(self, user):
        msg = get.new_curriculum(self.db, user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    # 跑操
    # service 做了缓存，这里不再缓存

    def pe_counts(self, user):
        msg = get.pe_counts(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    # 图书馆借书信息
    # 暂时使用旧版服务

    def rendered(self, user):
        msg = get.rendered(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    # GPA

    def gpa(self, user):
        msg = get.gpa(self.db, user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def update_gpa(self, user):
        msg = update.gpa(self.db, user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    # SRTP
    def srtp(self, user):
        msg = get.srtp(self.db, user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def update_srtp(self, user):
        msg = update.srtp(self.db, user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    # 调戏
    def play(self, user):
        msg = play.update(self.db, user)  # u'=。= 暂不接受调戏'
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def simsimi(self, content, user):
        msg = play.simsimi(content, user)
        try:
            self.write(self.wx.response_text_msg(msg.decode('utf-8')))
        except UnicodeEncodeError:
            self.write(self.wx.response_text_msg(msg))
        except:
            self.write(self.wx.response_text_msg(u'encode error'))
        self.finish()

    #一卡通
    def card(self, user):
        msg = get.card(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    #人文讲座
    def lecture(self, user):
        msg = get.lecture(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    #校园网
    def nic(self, user):
        msg = get.nic(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    #教务处
    def jwc(self, user):
        msg = get.jwc(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    #图书馆搜索图书
    def searchlib(self, user):
        msg = get.searchlib(user, self.wx.sub_content)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    #校车
    def schoolbus(self, user):
        msg = get.schoolbus(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def phylab(self, user):
        msg = get.phylab(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def lecturenotice(self, user):
        msg = get.lecturenotice(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def grade(self, user):
        msg = get.grade(self.db, user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    #xiao quan yi
    def quanyi_info(self, user):
        msg = quanyi.quanyi(self.db, user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    # ticket
    def ticket(self, user):
        self.write(ticket_handler(self.wx.ticket_type, user, self.db, self.wx))
        self.finish()
    #  弹幕
    def dm(self,user):
        get.dm(user,self.wx.sub_content)
        msg = u'发送弹幕成功'
        self.write(self.wx.response_text_msg(msg))
        self.finish()
    # 宿舍
    def room(self,user):
        msg = get.room(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def yuyue(self,user):
        msg = get.yuyue(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()
    def xiaoli(self,user):
        self.write(self.wx.response_pic_msg(u'校历','http://mmbiz.qpic.cn/mmbiz/RmfKVHqzAibS1f3xFqJqxeDkEgFzAlrD0Q4JPjKOgwdkLmtub3NWuLsx78wltCz4bV7b0DoeBG8KRVmR4d8ffKg/640?wx_fmt=jpeg&tp=webp&wxfrom=5&wx_lazy=1',u'点击查看详细','http://mp.weixin.qq.com/s?__biz=MjM5NDI3NDc2MQ==&mid=400874492&idx=1&sn=2ed0d9882fdc78a3c2e4f5dfc4565802#rd'))
        self.finish()

    def exam(self,user):
        msg = get.exam(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()
    def feedback(self,user):
        msg = u'\n<a href="http://115.28.27.150/service/feedback">点我进行反馈哦~</a>'
        self.write(self.wx.response_text_msg(msg))
        self.finish()
    def tice(self,user):
        msg = get.tice(user)
        self.write(self.wx.response_text_msg(msg))
        self.finish()
    # 其他
    def change_user(self, user):
        msg = u'当前用户为：%s \n\n\n<a href="%s/register/%s">点击重新绑定</a>' % (
            user.cardnum, LOCAL, self.wx.openid)
        msg += u'\n<a href="http://115.28.27.150/service/feedback">点我进行反馈哦~</a>'
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def help(self, user):
        msg = u'<a href="http://mp.weixin.qq.com/s?__biz=MjM5NDI3NDc2MQ==&mid=202009235&idx=1&sn=6659475ca9c4afd40c46b32c6a45ecb2#rd"> =。= 点我查看使用说明 </a>'
        self.write(self.wx.response_text_msg(msg))
        self.finish()

    def nothing(self, user):
        msg = u'无法识别命令.\n想要调戏小猴别忘了点一下[调戏]\n想要找图书前面别忘了加上"ss"'
        msg += u'\n<a href="http://115.28.27.150/service/feedback">点我进行反馈哦~</a>'
        msg += u'\n么么哒'
        self.write(self.wx.response_text_msg(msg))
        self.finish()

if __name__ == '__main__':
    tornado.options.parse_command_line()
    Application().listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
