# 第一章 信封
信封里只有一条消息.
## 1. 信封
信封作为信息载体,最小计算单位. 信封最后还要投放到信箱里(inbox)

## 2. 消息体
actor接收消息(这里不仅仅是简单的字符串信息)，也可能是修改自身属性和方法调用.
这里统一成为属性attr.

- actor 调用方法
- actor 修改属性值
- actor 获得属性值
- 普通的文本信息
 
本质是符合actor原则:
> 自身修改自身的状态.

## 知识点：
使用dataclass 替代 namedtuple

```@dataclass
class _ActorStop:
    pass
```
两者的比较: https://medium.com/@jacktator/dataclass-vs-namedtuple-vs-object-for-performance-optimization-in-python-691e234253b9

## Usage
参考测试文件.

## 扩充
可以考虑给信封添加时间戳等meta data.

