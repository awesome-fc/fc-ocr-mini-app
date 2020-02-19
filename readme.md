# 在支付宝小程序上使用函数计算实现OCR

## 介绍
A OCR demo on alipay mini program using alicloud function compute as backend.

1. Upload image to OSS bucket via alipay miniprogram client
2. A function is triggered and process image uploaded, extract OCR result and save the result in a bucket
3. Get OCR result back on mini program


## 使用

1. 函数计算开发环境，使用[Fun工具](https://help.aliyun.com/document_detail/64204.html) 进行函数部署
2. OSS bucket创建，存储上传的图片，本demo需要创建两个bucket
3. 开启阿里云OCR服务: [通用类图片文字识别](https://ai.aliyun.com/ocr/general?spm=5176.182739.1280361.96.69111d8avKcFFG)
4. 替换python代码中的`<>`中的内容为你配置，然后`fun deploy`
5. 运行支付宝小程序client端，上传图片，得到识别结果


更多介绍请查看[intro.md](http://gitlab.alibaba-inc.com/awesome-fc/fc-ocr/blob/master/intro.md)
