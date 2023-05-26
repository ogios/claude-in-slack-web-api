"use strict";
const http = require("http"),
    fs = require("fs"),
    path = require("path"),
    url = require("url");
// 获取当前目录
var root = path.resolve();
var config = fs.readFileSync(__dirname+"/../config.json");
config = JSON.parse(config);

// 创建服务器
var sever = http.createServer(function(request,response){
    var pathname = url.parse(request.url).pathname;
    var filepath = __dirname + pathname
    // 获取文件状态
    fs.stat(filepath,function(err,stats){
        if(err){
      // 发送404响
            response.writeHead(404)
            response.end("404 Not Found.");
        }else{
            if (fs.statSync(filepath).isDirectory()){
                response.writeHead(404)
                response.end("404 Not Found.");
                return;
            }
            response.writeHead(200);
            // console.log(filepath)
            if (filepath.endsWith("index.html")){
                let data = fs.readFileSync(filepath).toString();
                data = data.replace(
                    /(<input[^>]*id="baseurl"[^>]*?)(>)/,
                    "<input hidden='hidden' id='baseurl' value='http://" + config.HOST + ":" + config.API_PORT +"'>"
                )
                response.end(data);
            } else {
                fs.createReadStream(filepath).pipe(response)
            }

        }
    });
});
var PORT = config.WEB_PORT
var HOST = "0.0.0.0"
sever.listen(PORT, HOST);
console.log('Sever is running at http://' + HOST + ':' + PORT + '/');

