# 第三章 Actor
![](.readme.markdown_images/acotr.png)
从图可以查看他们之间并不是继承关系，还是包裹.
- An actor被看作并发的，通用的计算基元。
- Actors能够接受和发送消息、
- 创建更多的Actors、
 - Actors 不和其他actor 不分享状态, 只能通过消息修改自身私有状态(避免需要任何的锁)。

## Actor 
Actors之间只能通过消息修改自身私有状态(避免需要任何的锁)。
每个Actor实例封装了自己相关的状态，并且和其他Actor处于物理隔离状态


## Actor Ref
Ref 就是对actor的包裹wrapper. 
Actor对象需要与外界隔离才符合Actor model的设计思想。
因此Actor是以ActorRef(引用)的形式展现给外界的，ActorRef作为对象，
可以被无限制地自由传递。Actor和ActorRef的这种划分使得所有操作都能够透明。
e.g. 重启Actor而不需要更新ActorRef、将实际Actor对象部署在远程主机上和向另外一个应用程序发送消息。更重要的是，
外界不可能直接得到Actor对象的内部状态，
除非这个Actor非常不明智地将内部状态暴露。

## Actor Proxy
代理actor_ref，中间人负责不同Actor或本地和远程的沟通。 就是proxy 在前面冲锋. 隐藏了很多内部细节， 不会暴力真实的actor.


## 扩展
 - 代理模式 proxy pattern 
 - actor_ref 可以使用with context 包裹.