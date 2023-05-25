var email = null;
var passwd = null;
var chatlog = document.querySelector('#chatlog');
var chatform = document.querySelector('#chatform');
// var login = $("#login");
var ws = new WebSocket("ws://127.0.0.1:0");
var boot_data = null;

function checkEmail(email){
    return !(email === null || !email.includes("@"));
}

function getEmail(){
    let st_email = window.localStorage.getItem("email");
    while (!checkEmail(st_email)){
        st_email = prompt("邮箱: ", st_email);
    }
    window.localStorage.setItem("email", st_email);
    return st_email;
}


function initLi(){
    let li = document.createElement('li');
    let left  = document.createElement("div");
    let right = document.createElement("div");
    left.setAttribute("class", "left");
    left.innerHTML = "<img src='./img/user.jpg' alt='头像'/>";
    right.setAttribute("class", "right");
    right.innerHTML = "<span> ... </span>";
    li.appendChild(left);
    li.appendChild(right);
    chatlog.appendChild(li);
}

function createWSSConnection(url){
    ws = new WebSocket(url);
    ws.onopen = function() {
        console.log('WebSocket 连接成功');
        let data = boot_data;
        let ok = data.ok;
        let step = data.step;
        let env = data.env;
        if (ok === true){
            alert("slack is online");
        } else {
            switch (step){
                case "done":
                    alert("slack is online");
                    break;
                case "checkIfLogin":
                    sendCode();
                    break;
                case "sendCode":
                    getTeamList();
                    break;
                default:
                    if (env === true){
                        let login = confirm("use env?");
                        checkIfLogin(login);
                    } else {
                        console.log(data.msg);
                        if (data.msg !== undefined){
                            if (data.msg === "Authorization expired"){
                                let if_login = confirm("Authorization has expired, login or not?");
                                if (if_login) checkIfLogin(false);
                            }
                        } else {
                            let login = confirm("no env detected, login?");
                            if (login === true)
                                checkIfLogin(false);
                        }
                    }
            }
        }
        initLi();
    };
    ws.onmessage = function(event) {
        let data = JSON.parse(event.data);
        console.log(data);
        let type = data.type;
        let ok = data.ok;
        switch (type){
            case "text":
                flushMessage(data);
                break;
            case "checkIfLogin":
                if (ok === true) sendCode()
                else alert(data.msg);
                break;
            case "sendCode":
                if (ok === true) getTeamList();
                else alert(data.msg);
                break;
            case "getTeamList":
                selectTeam(data.msg);
                break;
            case "selectTeam":
                if (ok === true) checkStatus(getEmail())
                else alert(data.msg);
                break;
            case "error":
                alert(data.msg);
                if (data.msg === "not_authed"){
                    alert("authorization is expired, ready to login.");
                    checkIfLogin(false);
                }
        }

        chatlog.scrollTop = chatlog.scrollHeight;
    };
}

function checkIfLogin(login){
    let data = {
        "type": "checkIfLogin",
        "msg": login,
    }
    ws.send(JSON.stringify(data));
    if (login === true){
        checkStatus(getEmail())
    }
}

function sendCode(){
    let code = "";
    while (true) {
        code = prompt("邮箱验证码: ")
        if (code.length === 6 || code.length === 7){
            let data = {
                "type": "sendCode",
                "msg": code,
            }
            ws.send(JSON.stringify(data));
            break;
        }
    }

}

function getTeamList(){
    let data = {
        "type": "getTeamList",
        "msg": "",
    }
    ws.send(JSON.stringify(data));
}

function selectTeam(teamlist){
    teamlist = JSON.parse(teamlist);
    let len = teamlist.length;
    let string = "";
    for (let i=0;i<len;i++){
        string += i + ". 工作区 - " + teamlist[i]['name'] + "\n";
    }
    string += "请选择工作区(数字): ";
    while (true){
        let option = prompt(string);
        try {
            option = parseInt(option);
            let data = {
                "type": "selectTeam",
                "msg": option,
            };
            ws.send(JSON.stringify(data));
            break;
        } catch (e){
            alert(e);
        }
    }
}

function checkStatus(email){
    $.baseURI = "http://127.0.0.1:80"
    $.get(
        "http://127.0.0.1:80/check?email=" + email,
        (data) => {
            data = JSON.parse(data);
            let ok = data.ok;
            boot_data = data;
            let url = data.url;
            ws.close();
            // let code = null;
            if (ok === false){
                if (data.msg === "Authorization expired"){
                    boot_data.env = false;
                    // let if_login = confirm("Authorization has expired, ready to login.");
                    // if (if_login) code = "checkIfLogin(false);"
                }
            }
            createWSSConnection(url);
            // if (code != null) eval(code);
        }
    )
}

function signin(){
    let st_email = window.localStorage.getItem("email");
    let email = prompt("邮箱", st_email);
    if (email !== null && email !== ""){
        window.localStorage.setItem("email", email);
        checkStatus(email);
    }
}

function flushMessage(js) {
    var status = js.status;
    var msg = js.msg;
    var user = js.user;
    if (status === false) {
        let li = chatlog.lastElementChild;
        let left = li.firstElementChild;
        let right = li.lastElementChild;
        right.lastElementChild.textContent = msg;
        let img = left.lastElementChild.getAttribute("src");
        if (!img.includes(user)) {
            left.lastElementChild.innerHTML = '<img src="./img/' + user + '.jpg" alt="头像">'
        }
    } else if (status === true) {
        chatlog.lastElementChild.lastElementChild.lastElementChild.textContent = msg;
        initLi();
    }
}

chatform.addEventListener('submit', function(event) {
    event.preventDefault();
    var input = document.querySelector('#message');
    var message = input.value;
    var data = {
        "email": window.localStorage.getItem("email"),
        "text": message
    };
    data = JSON.stringify(data);

    input.value = '';

    $.ajax({
        type: "POST",
        url: "http://127.0.0.1/postMessage",
        data: data,
        success: (data) => {
            data = JSON.parse(data);
            let ok = data.ok;
            if (ok === false)
                alert("send messgae fatal: " + data.msg);
        },
        contentType: "application/json",
        dataType: "text",
    })
});

$(document).ready(() => {
    signin();
})