# dbOpers
## 项目简介
本项目是一个微型mysql操作前端,后端使用python的webpy,前端采用angular,重前端设计.项目参考 [violin/zealot](https://github.com/violin/zealot)

## 运行方式
  1. pip install web.py orator 安装 建议使用pyenv环境
  2. 配置 dbconf.py 
  3. python server.py 后端端口
  4. 配置nginx
    * / => html/index.html
    * /static => 指向静态目录 static
    * ~ .json$ => 反代到webpy开的服务端口
    
## 特色
在 zealot 基础上去掉也些并不是用很多的功能,兼容各浏览器,操作更流畅,查询语句带简单的自动补全
