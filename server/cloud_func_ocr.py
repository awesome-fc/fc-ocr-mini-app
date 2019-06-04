# coding=utf-8
'''
A OCR demo on alipay mini program using alicloud function compute as backend. 

1. User upload image to OSS bucket via alipay miniprogram client
2. A function is triggered and process image uploaded, extract OCR result and save the result in bucket
3. User get OCR result back on mini program

'''
 
import oss2, json
import logging
import base64
import urllib, urllib2, sys
import ssl
import json
import time
from cgi import parse_qs, escape
import cgi
import io


logger = logging.getLogger()

ocr_image_bucket = '<your_ocr_image_bucket_name>'  
ocr_text_bucket = '<your_ocr_text_bucket_name>'   
oss_endpoint = '<your_oss_endpoint>'
secret_id = '<your_secret_id>'   
secret_key = '<your_secret_key>'  
ocr_api_appcode = '<your_ocr_api_appcode>' 

ocr_api_url = 'https://ocrapi-advanced.taobao.com/ocrservice/advanced'


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


def upload_ocr_image(environ, start_response):
    '''
    upload ocr image function triggered by http request
    '''
    try:
        content = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, keep_blank_values=True)
        for key in content.keys():
            image_binary = content.getvalue(key)
            auth = oss2.Auth(secret_id, secret_key)
            bucket = oss2.Bucket(auth, oss_endpoint, ocr_image_bucket)
            bucket.put_object(key, image_binary)
        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return ['upload image success']
    except (ValueError):
        return ['upload_ocr_image failed']


def get_ocr_result(environ, start_response):
    '''
    get ocr result function triggered by http request
    '''
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        request_body = environ['wsgi.input'].read(request_body_size)
        res_json = json.loads(request_body)
        auth = oss2.Auth(secret_id, secret_key)
        bucket = oss2.Bucket(auth, oss_endpoint, ocr_text_bucket)
        ocr_res = bucket.get_object(str(res_json['key'])).read()
        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [str(ocr_res).encode('utf8')]
    except (ValueError):
        return ['get_ocr_result failed']
    
