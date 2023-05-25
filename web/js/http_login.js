var chatlog = document.querySelector('#chatlog');
var chatform = document.querySelector('#chatform');
var ws = new WebSocket("ws://127.0.0.1:0");

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
    console.log("connecting to " + url);
    ws = new WebSocket(url);
    ws.onopen = function() {
        console.log('connection established');
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

function Login_callback(data){
    data = JSON.parse(data);
    let ok = data.ok;
    if (ok === false) {
        alert(data.msg);
        return;
    }
    let next_step = data.next_step;
    matchStep(next_step);
}

function _Login(data, type, step){
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1/login?type=" + type + "&step=" + step,
        data: data,
        success: Login_callback,
        contentType: "application/json",
        // dataType: "text",
    })
}


function Login_init(){
    let data = JSON.stringify({"email": getEmail()});
    _Login(
        data,
        "email",
        "init",
    )
}

function Login_sendCode(){
    let code = "";
    while (true) {
        code = prompt("verification code: ")
        if (code.length === 6 || code.length === 7){
            let data = {
                "email": getEmail(),
                "code": code,
            }
            _Login(
                JSON.stringify(data),
                "email",
                "sendCode"
            )
            break;
        }
    }

}

function getTeamList(){
    $.get(
        "http://127.0.0.1/getTeamList?email=" + getEmail(),
        (data) => {
            data = JSON.parse(data);
            selectTeam(data);
        }
    )
}

function selectTeam(teamlist){
    // teamlist = JSON.parse(teamlist);
    let len = teamlist.length;
    let string = "";
    for (let i=0;i<len;i++){
        string += i + ". workspace - " + teamlist[i]['name'] + "\n";
    }
    string += "choose your work space (index): ";
    while (true){
        let option = prompt(string);
        try {
            option = parseInt(option);
            let data = {
                "email": getEmail(),
                "option": option,
            };
            _Login(
                JSON.stringify(data),
                "email",
                "selectTeam"
            );
            break;
        } catch (e){
            alert(e);
        }
    }
}

function getDAndSave(){
    _Login(
        JSON.stringify({"email": getEmail()}),
        "email",
        "getDAndSave"
    );
}

function useEnv(){
    $.get(
        "http://127.0.0.1:80/env?email=" + getEmail(),
        (data) => {
            data = JSON.parse(data);
            let ok = data.ok;
            if (ok === true){
                if (data.auth === true) {
                    alert(data.msg);
                    connectToWSS();
                }
                else {
                    let login = confirm("the env loaded seems to be expired, login?");
                    if (login === true) Login_init();
                }
            } else alert(data.msg);
        }
    )
}

function connectToWSS(){
    $.get(
        "http://127.0.0.1/connect?email=" + getEmail(),
        (data) => {
            data = JSON.parse(data);
            let ok = data.ok;
            if (ok === true) alert("slack connected");
            else alert(data.msg);
        }
    )
}


function matchStep(next_step){
    switch (next_step){
        case "init":
            Login_init();
            break;
        case "sendCode":
            Login_sendCode();
            break;
        case "selectTeam":
            getTeamList();
            break;
        case "getDAndSave":
            getDAndSave();
            break;
        case "done":
            alert("slack is online.");
            connectToWSS();
    }
}

function checkStatus(email){
    $.baseURI = "http://127.0.0.1:80"
    $.get(
        "http://127.0.0.1:80/check?email=" + email,
        (data) => {
            data = JSON.parse(data);
            let ok = data.ok;
            let url = data.url;
            let next_step = data.next_step;
            let env = data.env;
            if (env === true){
                let useenv = confirm("env has been saved for this account, load it or not?")
                if (useenv === true) useEnv();
                ws.close();
                createWSSConnection(url);
            } else{
                if (ok === true) {
                    let if_login = confirm("No env detected for this account, login?");
                    if (if_login === false) return;
                    matchStep(next_step);
                    ws.close();
                    createWSSConnection(url);
                }
            }

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
    let status = js.status;
    let msg = js.msg;
    let user = js.user;
    let li = chatlog.lastElementChild;
    let left = li.firstElementChild;
    let right = li.lastElementChild;
    right.lastElementChild.textContent = msg;
    let img = left.lastElementChild.getAttribute("src");
    if (!img.includes(user)) {
        left.innerHTML = '<img src="./img/' + user + '.jpg" alt="头像">'
    }
    if (status === false) {
        // let img = left.lastElementChild.getAttribute("src");
        // if (!img.includes(user)) {
        //     left.innerHTML = '<img src="./img/' + user + '.jpg" alt="头像">'
        // }
    } else if (status === true) {
        // chatlog.lastElementChild.lastElementChild.lastElementChild.textContent = msg;
        initLi();
    }
}

chatform.addEventListener('submit', function(event) {
    event.preventDefault();
    let input = document.querySelector('#message');
    let message = input.value;
    if (message.trim() === "/reset"){
        $.get(
            "http://127.0.0.1/execCmd?email=" + getEmail() + "&cmd=" + "/reset",
            (data) => {
                data = JSON.parse(data);
                if (data.ok === false) alert(data.msg);
            }
        )
        return;
    }
    let data = {
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
        // dataType: "text",
    })
});

$(document).ready(() => {
    signin();
})