Page({

  data: {
    inputValue: '',
  },

  onBlur(e) {
    this.setData({
      inputValue: e.detail.value,
    });
  },

  // 选择并上传图片
  attach() {
    my.chooseImage({
      chooseImage: 1,
      success: res => {
        const path = res.apFilePaths[0];
        console.log(path)
        var key = path
        my.uploadFile({
          url: 'https://1897532499842484.cn-shanghai.fc.aliyuncs.com/2016-08-15/proxy/test/upload_image/',
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
                url: 'https://1897532499842484.cn-shanghai.fc.aliyuncs.com/2016-08-15/proxy/test/get_ocr_result/',
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
});
