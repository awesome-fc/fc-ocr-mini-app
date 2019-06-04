# 10分钟使用阿里云函数计算构建你的OCR智能识别小程序

本文介绍使用支付宝小程序与函数计算的完成OCR光学字符识别的例子，十分钟快速开发一个轻量级可扩展应用


## 背景介绍
随着小程序的普遍流行，轻量级的应用开发越来越受到开发者们的关注，与此同时随着后端技术的Serverless化的优点逐渐明显，二者结合能快速构建高可用弹性的小程序，相信你已经迫不及待了，那就快点跟我来十分钟上手小程序和函数计算吧！

- 函数计算
    - 阿里云函数计算是事件驱动的全托管计算服务，无需管理服务器等基础设施，只需编写代码并上传，函数计算会为您准备好计算资源，以弹性、可靠的方式运行您的代码

    - 借助函数计算和其他云端服务的集成，开发者只需要编写少量代码就可以串联多个服务完成复杂的功能，大大提高开发效率
  

- 本教程使用函数计算作为小程序后端实现，具有以下优点
     - 开发部署过程更简单：开发者们只需要关注业务逻辑本身，也只需要实现业务逻辑本身，

     - 应用稳定性可用性更高：函数计算为用户准备弹性、可靠的计算资源，具有根据流量自动scale特性

     - 节省系统资源：函数计算的 Serverless 与云服务器最大的不同之处在于,云服务器需要一直运行，而函数计算是按需计算。按需计算就意味着，在请求到来的时候，才运行函数，没有请求的时候，不耗费资源



- 应用结构：

    ![fc_ocr_flow](http://git.cn-hangzhou.oss-cdn.aliyun-inc.com/uploads/serverless/admin-service/2e6860df540d8e8e5e77f9e9e70b1cea/fc_ocr_flow.png)

    1. 在小程序客户端上传图片，`http trigger`触发`upload_ocr_image`函数，函数接收文件上传到OSS

    2. OSS存入新图片，将触发`process_image`函数，读取新加入的图片，并调用`Vision API`进行字符识别和提取

    3. 将识别结果存储回OSS

    4. 小程序客户端请求识别结果，`http trigger`触发`get_ocr_result`函数，得到结果
 

## 使用方法

### 1. 开发环境准备工作

- [阿里云控制台获取获取`SecretId` 和`SecretKey`](https://help.aliyun.com/knowledge_detail/38738.html)

- 开通函数计算，熟悉函数功能[函数功能](https://help.aliyun.com/product/50980.html)

-  开启阿里云OSS服务，[创建bucket](https://help.aliyun.com/document_detail/31885.html?spm=a2c4g.11186623.6.567.277328bchsKc61)，存储上传的图片和识别结果，本demo需要创建两个bucket


- 开启阿里云OCR服务，具有免费试用次数: [通用类图片文字识别](https://ai.aliyun.com/ocr/general?spm=5176.182739.1280361.96.69111d8avKcFFG) ，获取`appcode`和服务`url`，需要填写到之后的配置里

- 进行支付宝小程序开发平台，按照例子创建应用：[体验小程序Demo](https://docs.alipay.com/mini/developer/todo-demo)


### 2. 编写函数
- 编写http请求函数：

    - 函数计算可以直接使用HTTP trigger触发，你可以快速编写任何接口，这里我们需要一个图片上传的接口：
    ```Python
    def upload_ocr_image(environ, start_response):
        '''
        upload ocr image function triggered by http request
        '''
        try:
            content = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, keep_blank_values=True)
            for key in content.keys():
                image_binary = content.getvalue(key)
                auth = oss2.Auth(oss_secret_id, oss_secret_key)
                bucket = oss2.Bucket(auth, oss_endpoint, ocr_image_bucket)
                bucket.put_object(key, image_binary)
            status = '200 OK'
            response_headers = [('Content-type', 'text/plain')]
            start_response(status, response_headers)
            return ['upload image success']
        except (ValueError):
            return ['upload_ocr_image failed']


    ```
    和一个请求图片OCR结果的函数：

    ```Python
    def get_ocr_result(environ, start_response):
        '''
        get ocr result function triggered by http request
        '''
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            res_json = json.loads(request_body)
            auth = oss2.Auth(oss_secret_id, oss_secret_key)
            bucket = oss2.Bucket(auth, oss_endpoint, ocr_text_bucket)
            ocr_res = bucket.get_object(str(res_json['key'])).read()
            status = '200 OK'
            response_headers = [('Content-type', 'text/plain')]
            start_response(status, response_headers)
            return [str(ocr_res).encode('utf8')]
        except (ValueError):
            return ['get_ocr_result failed']

    ```

- 编写OCR处理函数：
   - 使用OSS trigger，当有图片上传的时候触发OCR函数：
   ```Python
   def process_image(event, context):
        '''
        process image function triggered by OSS when a image file is uploaded
        '''
        evt = json.loads(event)
        evt = evt['events'][0]
        bucket_name = evt['oss']['bucket']['name']
        endpoint = 'oss-' +  evt['region'] + '.aliyuncs.com'
        obj_key = evt['oss']['object']['key']
        logger.info('New image uploaded: '  + str(obj_key))
        creds = context.credentials
        auth = oss2.StsAuth(creds.access_key_id, creds.access_key_secret, creds.security_token)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        image_data = bucket.get_object(obj_key).read()
        detect_word_list = detect_text(image_data)
        text_bucket = oss2.Bucket(auth, endpoint, ocr_text_bucket)
        text_bucket.put_object(obj_key + '_ocr.txt', ' '.join(detect_word_list).encode(encoding='UTF8'))
        return 'Processed image file success, text can be seen in the text bucket'
   ```


- 编写Vision Api 接口：
   - 直接请求阿里云OCR服务接口:
   ```Python
    def detect_text(image_data):
        encoded_image = base64.b64encode(image_data)
        detect_word_list = text_detect_api(encoded_image)
        logger.info("Detect word list : " + ' '.join(detect_word_list))
        return detect_word_list


    def text_detect_api(encodestr):
        method = 'POST'
        bodys = {}
        bodys['img'] = encodestr
        bodys['prob'] = 'false'
        bodys['charInfo'] = 'false'
        bodys['rotate'] = 'false'
        bodys['table'] = 'false'
        post_data = json.dumps(bodys).encode(encoding='UTF8')
        request = urllib2.Request(ocr_api_url, post_data)
        request.add_header('Authorization', 'APPCODE ' + ocr_api_appcode)
        request.add_header('Content-Type', 'application/json; charset=UTF-8')
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        response = urllib2.urlopen(request, context=ctx)
        content = response.read()
        logger.info("text detection res: " + str(content))
        word_list = []
        words_info = json.loads(content)['prism_wordsInfo']
        for info in words_info:
            word_list.append(info['word'].encode('utf8'))
        return word_list
   
   ```



### 3. 编写支付宝小程序
OCR识别的代码：
```JavaScript
// 选择并上传图片
  attach() {
    my.chooseImage({
      chooseImage: 1,
      success: res => {
        const path = res.apFilePaths[0];
        console.log(path)
        var key = path
        my.uploadFile({
          url: '<upload-image-endpoint>',
          fileType: 'image',
          fileName: key,
          filePath: path,
          success: (ret) => {
            var start=new Date().getTime();
            var n = 2000
            while(true) {
              if(new Date().getTime()- start > n) break;
            }
            var resKey = key + '_ocr.txt'
            my.request({
                url: '<get-result-endpoint>',
                method: 'POST',
                data: {
                  key: resKey
                },
                dataType: 'json',
                success: function(Res) {
                  my.alert({ content: 'Get OCR Result = \n' + Res.data});
                },
                fail: function(Res) {
                  my.alert({content: 'get ocr result fail:' + Res.errorMessage});
                }
            });
          },
        });
      },
    });
  },

```

### 4. 部署函数
- 编写函数部署yaml文件：

    ```yaml
    ROSTemplateFormatVersion: '2015-09-01'
    Transform: 'Aliyun::Serverless-2018-04-03'
    Resources:
    test:
        Type: 'Aliyun::Serverless::Service'
        Properties:
        Policies:
            - AliyunOSSFullAccess # Managed Policy
            - AliyunLogFullAccess # Managed Policy
        LogConfig:
            Project: func-func-log
            Logstore: func-test

        ocr_extract:
        Type: 'Aliyun::Serverless::Function'
        Properties:
            Handler: cloud_func_ocr.process_image
            Runtime: python2.7
            Timeout: 60
            MemorySize: 512
            CodeUri: './'

        upload_image:
        Type: 'Aliyun::Serverless::Function'
        Properties:
            Handler: cloud_func_ocr.upload_ocr_image
            Runtime: python2.7
            Timeout: 60
            MemorySize: 512
            CodeUri: './'
        Events:
            http-trigger:
            Type: HTTP
            Properties:
                AuthType: ANONYMOUS
                Methods: ['GET', 'POST', 'PUT']
        
        get_ocr_result:
        Type: 'Aliyun::Serverless::Function'
        Properties:
            Handler: cloud_func_ocr.get_ocr_result
            Runtime: python2.7
            Timeout: 60
            MemorySize: 512
            CodeUri: './'
        Events:
            http-trigger:
            Type: HTTP
            Properties:
                AuthType: ANONYMOUS
                Methods: ['GET', 'POST', 'PUT']

    ```

- 更改配置：替换python代码中的`<>`中的内容为你自己的相关配置

- 使用[Fun工具](https://help.aliyun.com/document_detail/64204.html) 进行函数部署，命令行运行`$ fun deploy`


### 5. 测试
运行小程序模拟器，可以上传一张图片，得到OCR识别结果

![img2](http://git.cn-hangzhou.oss-cdn.aliyun-inc.com/uploads/serverless/fc-canary/00bf595ce7e7092eae49b0cd765cca7a/img2)




## 总结

本文介绍了支付宝小程序和函数计算结合的一个简单的案例，通过简单的开发步骤，能够快速构建弹性高可用的云端小程序来；当然本案例介绍的例子很简单，更多的可能性还等待着你们来探索！