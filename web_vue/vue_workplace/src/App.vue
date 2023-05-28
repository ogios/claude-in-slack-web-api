<script setup>
</script>


<template>
    <!--    <img src="./assets/user.jpg">-->
    <h1>Chat with claude</h1>
    <div id="chatlog" style="width: 100%; height: 80%">
        <ul id="chatlog">
            <li v-for="message in messages">
                <div>
                    <img alt="avatar" v-bind:src=message.avatar />
                </div>
                <div>
                    <span>{{ message.text }}</span>
                </div>
            </li>
        </ul>
    </div>
    <div
        :style="{boxShadow: `var(--el-box-shadow-light)`}"
        style=" bottom: 0; display: flex; justify-content: space-between;align-items: center; border-top: black; border-radius: 15px"
    >

        <el-input
            v-model="newMessage"
            maxlength="2000"
            placeholder="Chat with the bot here"
            rows="5"
            show-word-limit
            style="width: 85%; margin: 30px"
            type="textarea"
            @keydown.enter.native="handleKeyCode($event)"
        />


        <el-button round style="width: 10%; right: 0; font-size: larger; margin: 20px" @click="sendMessage"> >
        </el-button>

    </div>

</template>

<script>
import {ref} from 'vue';
import {provide, inject} from 'vue';
import $ from 'jquery'
import {ElMessage, ElMessageBox} from 'element-plus';

export default {

    setup() {
        // var chatlog = document.querySelector('#chatlog');
        var ws = new WebSocket("ws://127.0.0.1:0");

        function getAPIUrl(path) {
            return baseurl + path
        }

        function checkEmail(email) {
            return !(email === null || !email.includes("@"));
        }

        async function getEmail() {

            let st_email = window.localStorage.getItem("email");
            while (!checkEmail(st_email)) {
                st_email = await ElMessageBox.prompt("Email: ", "Login to slack", {
                    confirmButtonText: 'OK',
                    cancelButtonText: 'Cancel',
                    inputPattern:
                        /[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?/,
                    inputErrorMessage: 'Invalid Email',
                    inputValue: st_email
                }).then((value) => {
                    return value.value;
                }).catch((reason) => {
                    return "";
                });
                console.log(st_email);
            }
            window.localStorage.setItem("email", st_email);
            console.log(st_email)
            return st_email;
        }

        function createWSSConnection(url) {
            console.log("connecting to " + url);
            ws = new WebSocket(url);
            ws.onopen = function () {
                console.log('connection established');
                setNewMessage();
            };
            ws.onmessage = function (event) {
                let data = JSON.parse(event.data);
                console.log(data);
                let type = data.type;
                let ok = data.ok;
                switch (type) {
                    case "text":
                        pushMessage(data);
                        break;
                    case "error":

                        ElMessage.error(data.msg);
                        // alert(data.msg);
                        if (data.msg === "not_authed") {
                            ElMessage.error("authorization is expired, ready to login.")
                            // alert("authorization is expired, ready to login.");
                            checkIfLogin(false);
                        }
                }
                $("#chatlog").scrollTop = $("#chatlog").scrollHeight;
            };
        }

        function Login_callback(data) {
            data = JSON.parse(data);
            let ok = data.ok;
            if (ok === false) {
                ElMessage.error(data.msg);
                // alert(data.msg);
                return;
            }
            let next_step = data.next_step;
            matchStep(next_step);
        }

        function _Login(data, type, step) {
            $.ajax({
                type: "POST",
                url: getAPIUrl("/login?type=" + type + "&step=" + step),
                data: data,
                success: Login_callback,
                contentType: "application/json",
            })
        }

        async function Login_init() {
            let data = JSON.stringify({"email": await getEmail()});
            _Login(
                data,
                "email",
                "init",
            )
        }

        async function Login_sendCode() {
            let code = "";
            while (true) {
                code = await ElMessageBox.prompt("Verification code: ", "Login to slack", {
                    confirmButtonText: 'OK',
                    cancelButtonText: 'Cancel',
                    inputErrorMessage: 'Invalid Code',
                }).then((value) => {
                    return value.value;
                }).catch((reason) => {
                    return "";
                });
                // code = prompt("verification code: ")
                if (code.length === 6 || code.length === 7) {
                    // console.log(await getEmail())
                    let data = {
                        "email": await getEmail(),
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

        async function getTeamList() {
            $.get(
                getAPIUrl("/getTeamList?email=" + await getEmail()),
                (data) => {
                    data = JSON.parse(data);
                    selectTeam(data);
                }
            )
        }

        async function selectTeam(teamlist) {
            // teamlist = JSON.parse(teamlist);
            let len = teamlist.length;
            let string = "";
            for (let i = 0; i < len; i++) {
                string += i + ". workspace - " + teamlist[i]['name'] + "\n";
            }
            string += "choose your work space (index): ";
            while (true) {
                let option = await ElMessageBox.prompt(string, "Login to slack", {
                    confirmButtonText: 'OK',
                    cancelButtonText: 'Cancel',
                    inputErrorMessage: 'Invalid index',
                }).then((value) => {
                    return value.value;
                }).catch((reason) => {
                    return "";
                });
                try {
                    option = parseInt(option);
                    let data = {
                        "email": await getEmail(),
                        "option": option,
                    };
                    _Login(
                        JSON.stringify(data),
                        "email",
                        "selectTeam"
                    );
                    break;
                } catch (e) {
                    ElMessage.error(e);
                    // alert(e);
                }
            }
        }

        async function getDAndSave() {
            _Login(
                JSON.stringify({"email": await getEmail()}),
                "email",
                "getDAndSave"
            );
        }

        async function useEnv() {
            $.get(
                getAPIUrl("/env?email=" + await getEmail()),
                (data) => {
                    data = JSON.parse(data);
                    let ok = data.ok;
                    if (ok === true) {
                        if (data.auth === true) {
                            ElMessage.success(data.msg);
                            // alert(data.msg);
                            connectToWSS();
                        } else {
                            ElMessageBox.confirm("the env loaded seems to be expired, login?", "Login")
                                .then(() => {
                                    Login_init();
                                })
                                .catch(() => {
                                    ElMessage.info("canceled.");
                                })
                            // let login = confirm("the env loaded seems to be expired, login?");
                            // if (login === true) Login_init();
                        }
                    } else
                        ElMessage.error(data.msg);
                    // alert(data.msg);
                }
            )
        }

        async function connectToWSS() {
            $.get(
                getAPIUrl("/connect?email=" + await getEmail()),
                (data) => {
                    console.log(data);
                    data = JSON.parse(data);
                    let ok = data.ok;
                    if (ok === true)
                        ElMessage.success("slack connected");
                    // alert("slack connected");
                    else
                        ElMessage.success(data.msg);
                    // alert(data.msg);
                }
            )
        }


        function matchStep(next_step) {
            switch (next_step) {
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
                    ElMessage.success("slack is online.");
                    // alert("slack is online.");
                    connectToWSS();
            }
        }


        function checkStatus(email) {
            $.get(
                getAPIUrl("/check?email=" + email),
                (data) => {
                    data = JSON.parse(data);
                    let ok = data.ok;
                    let url = data.url;
                    let next_step = data.next_step;
                    let env = data.env;
                    if (env === true) {
                        ElMessageBox.confirm("env has been saved for this account, load it or not?", "Login")
                            .then(() => {
                                useEnv();
                            })
                            .catch(() => {
                                ElMessage.info("canceled.");
                            });
                        // let useenv = confirm("env has been saved for this account, load it or not?")
                        // if (useenv === true) useEnv();
                        ws.close();
                        createWSSConnection(url);
                    } else {
                        if (ok === true) {
                            ElMessageBox.confirm("No env detected for this account, login?", "Login")
                                .then(() => {
                                    matchStep(next_step);
                                    ws.close();
                                    createWSSConnection(url);
                                })
                                .catch(() => {
                                    ElMessage.info("canceled.");
                                });
                            // let if_login = confirm("No env detected for this account, login?");
                            // if (if_login === false)
                        }
                    }

                }
            )
        }

        function refreshMessage(user, msg) {
            messages.value[messages.value.length - 1]["text"] = msg;
            messages.value[messages.value.length - 1]["avatar"] = (user === "user") ? "./assets/user.jpg" : "./assets/claude.jpg";
        }

        function setNewMessage() {
            messages.value.push({
                id: messages.value.length + 1,
                avatar: "./assets/user.jpg",
                text: "...",
            })
        }

        function signin() {
            let st_email = window.localStorage.getItem("email");
            ElMessageBox.prompt("Email: ", "Login to slack", {
                confirmButtonText: 'OK',
                cancelButtonText: 'Cancel',
                inputPattern:
                    /[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?/,
                inputErrorMessage: 'Invalid Email',
                inputValue: st_email
            }).then((value) => {
                // console.log("yes");
                console.log(value.value);
                window.localStorage.setItem("email", value.value);
                checkStatus(value.value);
                // console.log("yesfsafsaf");
            }).catch((reason) => {
                ElMessage.info("canceled.")
            })
        }

        function pushMessage(js) {
            let status = js.status;
            let msg = js.msg;
            let user = js.user;
            refreshMessage(user, msg);
            if (status === true) {
                setNewMessage();
            }
        }


        const messages = ref([
            // {id: 1, avatar: '/src/assets/user.jpg', text: '你好'},
            // {id: 2, avatar: '/src/assets/claude .jpg', text: '你也好'},
        ]);
        const newMessage = ref('');

        async function sendMessage() {
            let message = newMessage.value;
            if (message.trim() === "/reset") {
                $.get(
                    getAPIUrl("/execCmd?email=" + await getEmail() + "&cmd=" + "/reset"),
                    (data) => {
                        data = JSON.parse(data);
                        if (data.ok === false)
                            ElMessage.error(data.msg);
                        // alert(data.msg);
                    }
                )
            } else {
                let data = {
                    "email": window.localStorage.getItem("email"),
                    "text": message
                };
                data = JSON.stringify(data);
                $.ajax({
                    type: "POST",
                    url: getAPIUrl("/postMessage"),
                    data: data,
                    success: (data) => {
                        data = JSON.parse(data);
                        let ok = data.ok;
                        if (ok === false)
                            ElMessage.error("send messgae fatal: " + data.msg);
                        // alert("send messgae fatal: " + data.msg);
                    },
                    contentType: "application/json",
                })
            }
            newMessage.value = '';
        }

        provide('sendMessage', sendMessage);

        // setNewMessage()
        // refreshMessage("user", "我发送");
        // setNewMessage();
        // ElMessage.info("hi")
        // ElMessage.success("hi");


        return {
            messages,
            newMessage,
            sendMessage,
            signin,
        };
    },

    methods: {
        handleKeyCode(event) {
            if (!event.ctrlKey) {
                event.preventDefault();
                this.handleSendText();
            } else {
                this.newMessage = this.newMessage + '\n';
            }
        },

        handleSendText() {
            this.sendMessage();
        },


    },

    created() {
        window.vuethis = this;
        this.signin();
    }

};


</script>

<style>
ul {
    list-style: none;
    margin: 0;
    padding: 0;
}

li {
    display: flex;
    align-items: center;
    /*margin-bottom: 50px;*/
    margin: 20px;
}

img {
    width: 40px;
    height: 40px;
    border-radius: 50%;
}

#chatlog span {
    margin-left: 10px;
}


body {
    margin: auto;
    width: 80%;
}

ul li {
    display: flex;

}

.left img {
    /*display: block;*/
    width: 50px;
    height: 50px;
}

.left {
    flex: 1;
    justify-content: center;
    align-items: center;
    /*border-right: 1px solid black;*/
    text-align: center;
}

.right {
    flex: 5;
    width: 200px;
    word-wrap: break-word;
    border-top: 1px solid black;
    border-bottom: 1px solid black;
    font-size: small;
}


#chatlog {
    width: 75vw;
    height: 60vh;
    overflow: auto;
    list-style: none;
    padding: 0;
}

#message {
    width: 75vw;
}

ul li {
    /*border: 1px solid black;*/
    margin-bottom: 10px;
}
</style>


<style scoped>
</style>
