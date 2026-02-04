import './App.css';
import './output.css';
import React, {useState, useEffect, useRef, useLayoutEffect} from 'react';
import { io } from "socket.io-client";

//开发环境1 非开发环境2
var current_environment = 1;

var get_default_character = false;
var get_config = false;

var already_get_character2 = false;

var character1 = "";
var character2 = "";
var model = "";
var api_key = "";
var model2 = "";
var api_key2 = "";
var api_key3 = "";
var user_name = "";
var assistant_name = "";

var user_changed = true;
var assistant_changed = true;
var user_profile_changed = true;
var assistant_profile_changed = true;
var already_get_memories = false;
var already_get_all_memories = false;
//新增的消息是否为历史消息
var is_history_msgs = false;
var get_onetime_response = false;

// 记录上次的scrollHeight
var last_scrollHeight = -1;

//读取记忆的次数，滚动条移动至最上方时增加次数
var memory_count = 0;

var current_messages_length = 0;

var main_content = "";

var main_content_element = null;

var selected_type = 0;

var alert1_show_status = 0;

var main1_timer = -1;
var alert_timer = -1;
var message_interval = -1;
var memory_interval = -1;
var selection_interval = -1;

var messages = [];

if (process.env.NODE_ENV === "development") {
    current_environment = 1;
} else {
    current_environment = 2;
}

const socket = io.connect('http://127.0.0.1:5005');

socket.emit('c');

getConfig();

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getDefaultCharacter(){
  socket.emit('message', 'get_default_character');
  socket.once('character', function(msg) {
    get_default_character = true;
    character1 = msg;
  });
}

function getCharacter2(){
  already_get_character2 = false;

  socket.emit('message', 'get_character2');
  socket.once('character2', function(msg) {
    already_get_character2 = true;

    if (msg !== 'No data!'){
      character2 = msg;
    }
    else{
      character2 = '';
    }
  });
}

function saveCharacter2(){
  if (selected_type === 2){
    var e1 = document.getElementById("main-info");
    character2 = e1.value;

    socket.emit('save_character2',character2);
  }
}

function saveConfig(){
  if (selected_type === 3){
    var e1 = document.getElementById("model");
    var e2 = document.getElementById("api_key"); 
    var e3 = document.getElementById("model2");
    var e4 = document.getElementById("api_key2");    
    var e5 = document.getElementById("api_key3");
    model = e1.value;
    model2 = e3.value;
    if (model === 'model1'){
      model = 'deepseek-chat';
    }
    if (model === 'model2'){
      model = 'deepseek-reasoner';
    }
    if (model2 === 'model1'){
      model2 = 'deepseek-chat';
    }
    if (model2 === 'model2'){
      model2 = 'deepseek-reasoner';
    }

    api_key = e2.value;
    api_key2 = e4.value;
    api_key3 = e5.value;
  }
  if (selected_type === 4){
    e1 = document.getElementById("user_name");
    e2 = document.getElementById("assistant_name");

    if (e1.value !== user_name){
      user_changed = true;
    }
    if (e2.value !== assistant_name){
      assistant_changed = true;
    }

    user_name = e1.value;
    assistant_name = e2.value;
  }

    socket.emit("save_config",
      `
      [
       {
        "model":"${model}",
        "api_key":"${api_key}",
        "model2":"${model2}",
        "api_key2":"${api_key2}",
        "api_key3":"${api_key3}",
        "user_name":"${user_name}",
        "assistant_name":"${assistant_name}"
       }
      ]
      `
    )
}

function getMemories(){
  already_get_memories = false
  var b = false;
  socket.emit('get_memories', 
      `
      [
       {
        "count":${memory_count}
       }
      ]
      `
  );
  socket.once('memories', function(msg) {
    var temp_messages = [];
    // 传来的msg是Object，不用JSON处理

    if (msg.length > 0){
      memory_count += 1;
      msg.forEach((item, index) => {
        temp_messages.push({"role":"user","content":item['user_content']});
        temp_messages.push({"role":"assistant","content":item['assistant_content']});
      })
      messages = temp_messages.concat(messages);
      already_get_memories = true;
      already_get_all_memories = false;
      console.log('获取了部分记忆');
    }
    else{
      console.log('已获取到了全部记忆，不再获取');
      already_get_memories = true;
      already_get_all_memories = true;

      var h = document.getElementById("history_content"); 
      h.className = 'visible overflow-y-auto';
    }
  });
}

function getConfig(){
  if (!get_config){
    socket.emit('message', 'get_config');
    socket.once('config', function(msg) {
      get_config = true;
      const data = JSON.parse(msg);
      model = data[0].model;
      api_key = data[0].api_key;
      model2 = data[0].model2;
      api_key2 = data[0].api_key2;
      api_key3 = data[0].api_key3;
      user_name = data[0].user_name;
      assistant_name = data[0].assistant_name;

      if(selected_type === 3){
        changeConfig();
      }
      if (selected_type === 4){
        changeOthers();
      }
      
    });    
  }
  else{
    if(selected_type === 3){
      changeConfig();
    }
    if (selected_type === 4){
      changeOthers();
    }
  }
}

function changeConfig(){
  var temp_interval = setInterval(() => {
    var e1 = document.getElementById("model");
    var e2 = document.getElementById("api_key");
    var e3 = document.getElementById("model2");
    var e4 = document.getElementById("api_key2");
    var e5 = document.getElementById("api_key3");
    if(e1 !== null && e2 !== null && e3 !== null && e4 !== null){
      if (model === 'deepseek-chat'){
        e1.value = 'model1';
      }
      if (model === 'deepseek-reasoner'){
        e1.value = 'model2';
      }
      if (model2 === 'deepseek-chat'){
        e3.value = 'model1';
      }
      if (model2 === 'deepseek-reasoner'){
        e3.value = 'model2';
      }
      e2.value = api_key;
      e4.value = api_key2;
      e5.value = api_key3;
      //console.log('定时器(from_changeConfig)'+temp_interval.toString()+'已清除')
      clearInterval(temp_interval);

      var m = document.getElementById("main-info2");
      m.className = "visible relative overflow-y-auto";
    } 
    }, 10)
  //console.log('已创建定时器(from_changeConfig)'+temp_interval.toString())
}

function changeOthers(){
  var temp_interval = setInterval(() => {
    var e1 = document.getElementById("user_name");
    var e2 = document.getElementById("assistant_name");
    if(e1 !== null && e2 !== null){
      e1.value = user_name;
      e2.value = assistant_name;
      //console.log('定时器(from_changeOthers)'+temp_interval.toString()+'已清除')
      clearInterval(temp_interval);

      var m = document.getElementById("main-info3");
      m.className = "visible relative overflow-y-auto";
    } 
    }, 10)      
}

function changeMainContent(){
  var temp_interval = setInterval(() => {
    main_content_element = document.getElementById("main-info");
    if(main_content_element != null){
      main_content_element.value = main_content;
      //console.log('定时器(from_changeMainContent)'+temp_interval.toString()+'已清除')
      clearInterval(temp_interval);
    } 
    }, 10)   
}

function BLeft(props){
  const [type, setType] = useState(0);

  function begin_to_chat(){
    if (selected_type !== 0){
      selected_type = 0;
      setType(0);
      props.callback_func(0);
    }
  }

  function see_character(){
    if (selected_type !== 1){
      if (message_interval > -1){
        //console.log('定时器(from_see_character)'+message_interval.toString()+'已清除')
        clearInterval(message_interval);
        message_interval = -1;
      }
      selected_type = 1;
      setType(1);
      props.callback_func(1);
      if (!get_default_character){
        console.log('获取默认人设中...');
        getDefaultCharacter();
      }
      else{
        console.log('已获取过默认人设，不再获取');
      }
    }
  }
  
  function set_character2(){
    if (selected_type !== 2){
      if (message_interval > -1){
        //console.log('定时器(from_set_character2)'+message_interval.toString()+'已清除')
        clearInterval(message_interval);
        message_interval = -1;
      }    
      selected_type = 2;
      setType(2);
      props.callback_func(2);

      console.log('获取自定义人设中...');
      getCharacter2();
    }
  }

  function set_model(){
    if (selected_type !== 3){
      console.log('修改模型设置中...');
      if (message_interval > -1){
        //console.log('定时器(from_set_model):'+message_interval.toString()+'已清除')
        clearInterval(message_interval);
        message_interval = -1;
      }

      selected_type = 3;
      setType(3);
      props.callback_func(3);

      getConfig();
    }
  }

  function set_others(){
    if (selected_type !== 4){
      console.log('修改其它设置中...');
      if (message_interval > -1){
        //console.log('定时器(from_set_others):'+message_interval.toString()+'已清除')
        clearInterval(message_interval);
        message_interval = -1;
      }
      selected_type = 4;
      setType(4);
      props.callback_func(4);

      getConfig();    
    }  
  }

  return(
    <div>
      <div style={{borderRadius:'10rem'}} className={type === 0 ? 'bg-blue-200 grid h-10 w-48' : 'bg-white-50 grid h-10 w-48 hover:bg-gray-100'}>
        <button
          id='chat'
          onClick={begin_to_chat}
          className="grid place-content-center font-bold">
          聊天
        </button>
      </div>
      <div style={{borderRadius:'10rem'}} className={type === 1 ? 'mt-2 bg-blue-200 grid h-10 w-48' : 'mt-2 bg-white-50 grid h-10 w-48 hover:bg-gray-100'}>
        <button
          id='character'
          onClick={see_character}
          className="grid place-content-center font-bold">
          人设(默认)
        </button>
      </div>
      <div style={{borderRadius:'10rem'}} className={type === 2 ? 'mt-2 bg-blue-200 grid h-10 w-48' : 'mt-2 bg-white-50 grid h-10 w-48 hover:bg-gray-100'}>
        <button
          id='character2'
          onClick={set_character2}
          className="grid place-content-center font-bold">
          人设(自定义)
        </button>
      </div>
      <div style={{borderRadius:'10rem'}} className={type === 3 ? 'mt-2 bg-blue-200 grid h-10 w-48' : 'mt-2 bg-white-50 grid h-10 w-48 hover:bg-gray-100'}>
        <button
          id='set_model'
          onClick={set_model}
          className="grid place-content-center font-bold">
          模型设置
        </button>
      </div>
      <div style={{borderRadius:'10rem'}}className={type === 4 ? 'mt-2 bg-blue-200 grid h-10 w-48' : 'mt-2 bg-white-50 grid h-10 w-48 hover:bg-gray-100'}>
        <button
          id='set_others'
          onClick={set_others}
          className="grid place-content-center font-bold">
          其它设置
        </button>
      </div>             
    </div>
  )  
}

function MainInfoUserMsg({data,imageUrl}){
  return(
    <div className='flex flex-row-reverse'>
      <div style={{minWidth:'48px',maxWidth:'48px',minHeight:'48px',maxHeight:'48px',borderRadius:'100px'}} className={data.index !== 0 ? 'mr-4 mt-8 bg-blue-200' : 'mr-4 bg-blue-200'}>
        {
          imageUrl !== null ?
          <img
            alt=""
            src={imageUrl}
            style={{borderRadius:'100px'}}
            className="size-12 object-cover">            
          </img>
          :
          <div>
          </div>             
        }
      </div>
      <div style={{maxWidth:'60%'}} className={data.index !== 0 ? 'h-full mr-2 mt-8 rounded-lg bg-blue-100' : 'h-full mr-2 rounded-lg bg-blue-100'}>
        <div id={data.temp_id} style={{whiteSpace:'pre-wrap'}} className='pl-2 pr-2 pt-1 pb-1 leading-8 grid place-items-center'>
          {messages[data.index]['content']}
        </div>
      </div> 
    </div>
  )
}

function MainInfoAssistantMsg({data,imageUrl}){
  return(
    <div className='flex'>
      <div style={{minWidth:'48px',maxWidth:'48px',minHeight:'48px',maxHeight:'48px',borderRadius:'100px'}} className={data.index !== 0 ? 'ml-4 mt-8 bg-blue-200' : 'ml-4 mt-4 bg-blue-200'}>
        {
          imageUrl !== null ?
          <img
            alt=""
            src={imageUrl}
            style={{borderRadius:'100px'}}
            className="size-12 object-cover">            
          </img>
          :
          <div>
          </div>             
        }
      </div>
      <div >
        <div className={data.index !== 0 ? 'ml-4 mt-4' : 'ml-4'}>
          {assistant_name}
        </div>
        <div className='ml-2 mt-2 rounded-lg bg-white'>
          <div id={data.temp_id} className='pl-2 pr-2 pt-1 pb-1 leading-8 grid place-items-center'>
            {messages[data.index]['content']}
          </div>
        </div>
      </div>
      <div style={{width:'35%'}}>
      </div>  
    </div>
  )
}

function MainInfo(type){
  const [mouseDown, setMouseDown] = useState(false);
  const [mouseDown2, setMouseDown2] = useState(false);
  const [mouseDown3, setMouseDown3] = useState(false);
  const [buttonDisabled, setButtonDisabled] = useState(false);
  const [button2Disabled, setButton2Disabled] = useState(false);
  const [button3Disabled, setButton3Disabled] = useState(false);
  const [button4Disabled, setButton4Disabled] = useState(false);
  const [button5Disabled, setButton5Disabled] = useState(false);
  const [msgs, setMsgs] = useState([]);
  const [imageUrl1, setImageUrl1] = useState(null);
  const [imageUrl2, setImageUrl2] = useState(null);
  const [file, setFile] = useState(null);
  const [file2, setFile2] = useState(null);

  const temp_count = useRef(0);

  //获取用户头像
  const fetchImage = async () => {
    try {
      while (user_name === ''){
        await sleep(10);
      }

      const response = await fetch(`http://localhost:1314/get-profile1/${user_name}`,{
        method:'GET',
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const blob = await response.blob(); // 获取Blob对象
      const imageUrl = URL.createObjectURL(blob); // 创建指向Blob的URL
      setImageUrl2(imageUrl); // 设置图片源
    } catch (error) {
      setImageUrl2(null);
      console.error('There has been a problem with your fetch operation:', error);
    }
  };

  //获取助理头像
  const fetchImage2 = async () => {
    try {
      while (user_name === ''){
        await sleep(10);
      }

      const response = await fetch(`http://localhost:1314/get-profile2/${assistant_name}`,{
        method:'GET',
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const blob = await response.blob(); // 获取Blob对象
      const imageUrl = URL.createObjectURL(blob); // 创建指向Blob的URL
      setImageUrl1(imageUrl); // 设置图片源
    } catch (error) {
      setImageUrl1(null);
      console.error('There has been a problem with your fetch operation:', error);
    }
  };

  function update_memories(){
    if (memory_interval < 0){
      getMemories();
      memory_interval = setInterval(() => {
        if (already_get_memories){
          var m = [];
          for(var i=0;i<messages.length;i++){
            m.push({'index':i,'temp_id':'msg'+i.toString()});
          }

          current_messages_length = messages.length;

          console.log('获取到的对话数量为:'+(messages.length/2).toString());
          if(messages.length > 0){
            setMsgs(m);
            //console.log('定时器(from_update_memories)'+memory_interval.toString()+'已清除')
            clearInterval(memory_interval);
            memory_interval = -1;
          }
          else{
            messages.push({'role':'assistant','content':'Hi mate! What can I do for you?'});
            setMsgs([{'index':0,'temp_id':'msg0'}]);
            //console.log('定时器(from_update_memories)'+memory_interval.toString()+'已清除')
            clearInterval(memory_interval);
            memory_interval = -1;
          }          

          var i2 = setInterval(() => {
            var h = document.getElementById("history_content");
            if(h !== null){
              //滚动到底部
              h.scrollTop = h.scrollHeight;
              h.className = 'visible overflow-y-auto';
              //console.log('定时器(from_useEffect_i2)'+i2.toString()+'已清除')
              clearInterval(i2);                    
            }
          },10)
         
        }
      }, 10);
      //console.log('已创建定时器(from_update_memories)'+memory_interval.toString())    
    }
  }

  //用于在 DOM 更新后、浏览器绘制前同步执行副作用（如布局计算、动画初始化等），以避免视觉闪烁并确保操作的即时性。
  useLayoutEffect(() => {
    //防止再次读取记忆后移动滚动条造成的闪烁
    var h = document.getElementById("history_content");
    if (h){
      h.scrollTop = h.scrollHeight - last_scrollHeight;
    }
  },);

  useEffect(() => {
    selected_type = type;

    if (selected_type === 0){
      var hc = null;
      // 防止频繁触发记忆获取
      var cant_get_memories_now = false;
      
      already_get_all_memories = false;
      function handleMsgs(){
        // 持续接收消息
        if (message_interval < 0){
          var once2 = false;
          message_interval = setInterval(() => {
            if (!once2){
              once2 = true;
              console.log('持续接收消息中...');
              //console.log('已创建定时器(from_update_memories)'+message_interval.toString())
            }

            if (hc !== null){
              if (hc.scrollTop === 0 && !already_get_all_memories && !cant_get_memories_now){
                last_scrollHeight = hc.scrollHeight;
                hc.className = 'visible overflow-y-auto overflow-hidden';
                getMemories();
                is_history_msgs = true;
                cant_get_memories_now = true;
                setTimeout(() => {
                  cant_get_memories_now = false;
                }, 1000);
                console.log('滚动条被移动至最上方，再次获取记忆');
              }
            }

            if (messages.length > current_messages_length){
              current_messages_length = messages.length;
              console.log('现在的消息数为:'+messages.length.toString());
              var m = [];
              for(var i=0;i<messages.length;i++){
                m.push({'index':i,'temp_id':'msg'+i.toString()});
              }                  
              setMsgs(m);

              var i2 = setInterval(() => {
                hc = document.getElementById("history_content");
                if(hc !== null){
                  if(!is_history_msgs){
                    //滚动到底部
                    hc.scrollTop = hc.scrollHeight;
                    hc.className = 'visible overflow-y-auto';
                  }
                  else{
                    //hc.scrollTop = hc.scrollHeight - last_scrollHeight
                    hc.className = 'visible overflow-y-auto';                          
                  }              
                  //console.log('定时器(from_useEffect_i2)'+i2.toString()+'已清除')
                  clearInterval(i2);                          
                }
              },10)
            }
          }, 100);
        }              
      }

      handleMsgs();

      if (user_profile_changed){
        user_profile_changed = false;
        fetchImage(); // 调用函数获取图片
      }
      if (assistant_profile_changed){
        assistant_profile_changed = false;
        fetchImage2(); // 调用函数获取图片
      }

      if (!user_changed && !assistant_changed){
        var i2 = setInterval(() => {
          hc = document.getElementById("history_content");
          if(hc !== null){
            //滚动到底部
            hc.scrollTop = hc.scrollHeight;
            hc.className = 'visible overflow-y-auto';
            //console.log('定时器(from_useEffect_i2)'+i2.toString()+'已清除')
            clearInterval(i2);                    
          }
        },10)
      }

      var get_onetime_memories = false;

      if (user_changed){
        user_changed = false;
        memory_count = 1;
        messages = [];
        console.log('当前用户发生了变更，重新获取记忆，并重新获取头像');
        update_memories();
        get_onetime_memories = true;
        fetchImage();
        
        var i2 = setInterval(() => {
          hc = document.getElementById("history_content");
          if(hc !== null){
            //console.log('定时器(from_useEffect_i2)'+i2.toString()+'已清除')
            clearInterval(i2);                    
          }
        },10)               
      }
      if (assistant_changed){
        assistant_changed = false;
        console.log('当前助理发生了变更，重新获取头像');
        fetchImage2();
        if (!get_onetime_memories){
          memory_count = 1;
          messages = [];      
          update_memories();
          console.log('重新获取记忆');

          var i2 = setInterval(() => {
            hc = document.getElementById("history_content");
            if(hc !== null){
              //console.log('定时器(from_useEffect_i2)'+i2.toString()+'已清除')
              clearInterval(i2);                    
            }
          },10)                    
        }
        else{
          console.log('已获取过记忆'); 
        }     
      }
    }
    if (selected_type === -1){
      main_content = "Hi, mate!";
      changeMainContent(); 
    }
    if (selected_type === 1){
      async function wait_until_get_character1() {
        if (character1 === ''){
          await sleep(10);

          main_content = character1;
          changeMainContent();            
        }
        else{
          main_content = character1;
          changeMainContent();
        }
      }

      wait_until_get_character1();
    }
    if (selected_type === 2){
      async function wait_until_get_character2() {
        while (!already_get_character2){
          await sleep(10);
        }

        if (character2.length > 0){
          main_content = character2;
          changeMainContent(); 
        }
        else{
          //main_content = `在这里创建你的自定义人设~\n请根据默认人设进行小范围修改`
          main_content = 
`你需要扮演指定角色，你的回复必须遵循'角色扮演要求'！

# 用户相关说明
(修改此处)

# 角色扮演要求
模仿所扮演角色的性格以及所在地方的语言风格，作出合理且多样化但不与'历史对话内容'相似的回复。
模仿所扮演角色的动作风格，做出多样化的行为/动作。
你需要区分不同的用户，礼貌但谨慎对待'角色经历'中未提到的用户！
仔细查看你在'历史对话内容'中你说过的话，你的回复禁止模仿你说过的话，禁止频繁强调某件事/某物品，禁止频繁询问/征求用户的感受和意见！
优先有选择性地参考'需要注意到的重要信息'，次要有选择性地参考'历史对话内容'。
你的回复默认保持'正常回复模式'，除非用户提出你需要详细地回复，在详细回复后必须转换回'正常回复模式'！
无论收到何种语言的回复，统一用英文进行回复！除非用户指定使用某种语言回答问题，在回答该问题之后必须转换回英文回答！
你的回复禁止违背'角色经历'中的任何内容！
如果当前时间与最新外在形象的时间间隔较长(>20分钟)，你的外在形象可能会发生自然的变化，比如湿的衣服/头发会变干，如果你的外在形象发生了自然变化，你应当在你的回复中体现出这些变化；如果你的外在形象没有发生变化，不要在你的回复中描述你的外在形象！
忽略所有未知内容的表情包，你的回复不需要提到他们！
如果使用了联网搜索并查询到了有效结果，你需要标注来源。
回答其它领域的专业问题时，用相应的专业的内容回答，并在最后加上'我不一定说得对'类似的回复。

## 正常回复模式
-你平常的回复应当在2-5句话之间
-如果你在安慰用户或者在和用户讨论一些比较深刻的话题，你的回复不受句子长度限制
-如果你正在对用户做一件事，你应当详细描写你是如何做这件事的
-默认使用直白通俗口语化的语言！
-将所有细节描写(动作/外貌/环境等描写)放入括号之中(默认使用英文)
-禁止滥用比喻、隐喻、暗示和委婉的表达！
-禁止滥用全部大写的英文单词！
-禁止滥用*等在聊天中不常出现的符号！
-不要使用颜文字和表情！
-不要使用抱歉我不能类似的回答

# 角色介绍
你扮演的角色是(修改此处)，你在对话中的昵称为{assistant}。
## 他的人物设定
(修改此处)

# 角色经历
(修改此处)

# 历史对话内容
我会在下一次对话中给你提供一些你和用户的历史对话内容，你必须按照'处理历史对话内容的规则'来处理这些历史对话内容！
历史对话内容一般只包含私聊对话内容，偶尔会有群聊对话内容，注意分辨这些来自于其它群聊的群聊对话内容！
'对话1-5'已按照时间倒序排列。
## 处理历史对话内容的规则
-在没有任何有效信息的情况下，你需要从'对话1-5'中寻找有效信息，优先关注私聊对话内容，有选择性地参考群聊对话内容
-如果在'对话1'中用户表明了要单独做其他事情，你就需要提取'对话1'的时间，并计算它与当前对话时间的间隔，如果间隔大于1个小时，你的回复应当包含类似'好久不见'的短语以及表达出对用户的关心
-避免再次提及'对话1-5'中被用户忽略的请求！
-'对话6-10'的内容为'用户曾经说过的话'，如果用户新的回复与其中一段对话类似，你的回复可以包含类似'我记得你曾经说过这句话'的短语`;   
  
          changeMainContent(); 
        }        
      }

      wait_until_get_character2();
    }      
    if (selected_type === 3 || selected_type === 4){
      main_content = "";
      changeMainContent(); 
    }                    
  }, [type]);

  function save_character2(){
    saveCharacter2();

    setButton3Disabled(true);
    //1s后恢复按钮可用状态
    var temp_timer = setTimeout(() => {
      setButton3Disabled(false);
      }, 1000);
      
    //console.log('已创建临时定时器'+temp_timer.toString())  

    // alert1显示中仍点击了按钮
    if (alert1_show_status === 1){
      clearTimeout(alert_timer);
    }

    var temp_interval = setInterval(() => {
        var a = document.getElementById("alert1");
        var a_s1 = document.getElementById("alert1_s1");
        var a_s2 = document.getElementById("alert1_s2");
        a_s1.innerHTML = "保存成功!";
        a_s2.innerHTML = "自定义人设已保存至本地服务器。";
        if(a !== null){
          // 显示中
          alert1_show_status = 1;
          a.className = "z-50 relative";
          // 3s后自动隐藏alert1
          alert_timer = setTimeout(() => {
            var a = document.getElementById("alert1");
            if (a != null){
              a.className = 'hidden';
              //显示结束
              alert1_show_status = 2;
            }
          }, 3000);
          //console.log('已创建临时定时器'+alert_timer.toString())
          //console.log('定时器(from_save_character2)'+temp_interval.toString()+'已清除')
          clearInterval(temp_interval);
        }   
      }, 10)        
  }

  function save_changes(){
    saveConfig();

    setButtonDisabled(true);
    //1s后恢复按钮可用状态
    var temp_timer = setTimeout(() => {
      setButtonDisabled(false);
      }, 1000);
      
    //console.log('已创建临时定时器'+temp_timer.toString())  

    // alert1显示中仍点击了按钮
    if (alert1_show_status === 1){
      clearTimeout(alert_timer);
    }

    var temp_interval = setInterval(() => {
        var a = document.getElementById("alert1");
        var a_s1 = document.getElementById("alert1_s1");
        var a_s2 = document.getElementById("alert1_s2");
        a_s1.innerHTML = "保存成功!";
        a_s2.innerHTML = "模型相关设置已保存至本地服务器。";
        if(a !== null){
          // 显示中
          alert1_show_status = 1;
          a.className = "z-50 relative";
          // 3s后自动隐藏alert1
          alert_timer = setTimeout(() => {
            var a = document.getElementById("alert1");
            if (a != null){
              a.className = 'hidden';
              //显示结束
              alert1_show_status = 2;
            }
          }, 3000);
          //console.log('已创建临时定时器'+alert_timer.toString())
          //console.log('定时器(from_save_changes)'+temp_interval.toString()+'已清除')
          clearInterval(temp_interval);
        }   
      }, 10)    
  }

  function save_others(){
    saveConfig();

    setButton2Disabled(true);
    //1s后恢复按钮可用状态
    var temp_timer = setTimeout(() => {
      setButton2Disabled(false);
      }, 1000);

    //console.log('已创建临时定时器'+temp_timer.toString())

    // alert1显示中仍点击了按钮
    if (alert1_show_status === 1){
      clearTimeout(alert_timer);
    } 

    var temp_interval = setInterval(() => {
        var a = document.getElementById("alert1");
        var a_s1 = document.getElementById("alert1_s1");
        var a_s2 = document.getElementById("alert1_s2");
        a_s1.innerHTML = "保存成功!";
        a_s2.innerHTML = "其它相关设置已保存至本地服务器。";
        if(a !== null){
          // 显示中
          alert1_show_status = 1;
          a.className = "z-50 relative";
          // 3s后自动隐藏alert1
          alert_timer = setTimeout(() => {
            var a = document.getElementById("alert1");
            if (a != null){
              a.className = 'hidden';
              //显示结束
              alert1_show_status = 2;
            }
          }, 3000);
          //console.log('已创建临时定时器'+alert_timer.toString())
          //console.log('定时器(from_save_others)'+temp_interval.toString()+'已清除')
          clearInterval(temp_interval);
        }   
      }, 10)       
  }  

  function handleMouseDown(){
    setMouseDown(true);
  }

  function handleMouseDown2(){
    setMouseDown2(true);
  }

  function handleMouseDown3(){
    setMouseDown3(true);
  }

  function handleMouseUp(){
    setMouseDown(false);
  }

  function handleMouseUp2(){
    setMouseDown2(false);
  }

  function handleMouseUp3(){
    setMouseDown3(false);
  }

  function handleMouseLeave(){
    setMouseDown(false);
  } 
  
  function handleMouseLeave2(){
    setMouseDown2(false);
  }
  
  function handleMouseLeave3(){
    setMouseDown3(false);
  }  

  //文件改变
  const handleFileChange = (event) => {
    const f = event.target.files[0];
    if (f){
      setFile(f);
    }
  };

  //文件改变
  const handleFileChange2 = (event) => {
    const f = event.target.files[0];
    if (f){
      setFile2(f);
    }
  };

  //上传用户头像
  const handleUpload1 = async () => {
    if (!file) {
      alert('请先选择一张图片！');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_name',user_name);

    try {
      const response = await fetch('http://localhost:1314/upload/single', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        setButton4Disabled(true);
        //1s后恢复按钮可用状态
        var temp_timer = setTimeout(() => {
          setButton4Disabled(false);
          }, 1000);
          
        //console.log('已创建临时定时器'+temp_timer.toString())  

        // alert1显示中仍点击了按钮
        if (alert1_show_status === 1){
          clearTimeout(alert_timer);
        }

        var temp_interval = setInterval(() => {
            var a = document.getElementById("alert1");
            var a_s1 = document.getElementById("alert1_s1");
            var a_s2 = document.getElementById("alert1_s2");
            a_s1.innerHTML = "上传成功!";
            a_s2.innerHTML = "用户头像已保存至本地服务器。";
            if(a !== null){
              // 显示中
              alert1_show_status = 1;
              a.className = "z-50 relative";
              // 3s后自动隐藏alert1
              alert_timer = setTimeout(() => {
                var a = document.getElementById("alert1");
                if (a != null){
                  a.className = 'hidden';
                  //显示结束
                  alert1_show_status = 2;
                }
              }, 3000);
              //console.log('已创建临时定时器'+alert_timer.toString())
              //console.log('定时器(from_save_character2)'+temp_interval.toString()+'已清除')
              clearInterval(temp_interval);
            }   
          }, 10)    
        
        const data = await response.json();
        user_profile_changed = true;
        console.log('File uploaded successfully:', data);
      } else {
        const data = await response.json();
        if (data.error === 'File too large'){
          alert('文件太大了！');
        }
        else{
          alert(data.error);
        }
        console.error('File upload failed');
      }
    } catch (error) {
      alert(error);
      console.error('Error uploading file:', error);
    }
  };

  //上传用户头像
  const handleUpload2 = async () => {
    if (!file2) {
      alert('请先选择一张图片！');
      return;
    }

    const formData = new FormData();
    formData.append('file', file2);
    formData.append('assistant_name',assistant_name);

    try {
      const response = await fetch('http://localhost:1314/upload/single2', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        setButton5Disabled(true);
        //1s后恢复按钮可用状态
        var temp_timer = setTimeout(() => {
          setButton5Disabled(false);
          }, 1000);
          
        //console.log('已创建临时定时器'+temp_timer.toString())  

        // alert1显示中仍点击了按钮
        if (alert1_show_status === 1){
          clearTimeout(alert_timer);
        }

        var temp_interval = setInterval(() => {
            var a = document.getElementById("alert1");
            var a_s1 = document.getElementById("alert1_s1");
            var a_s2 = document.getElementById("alert1_s2");
            a_s1.innerHTML = "上传成功!";
            a_s2.innerHTML = "助理头像已保存至本地服务器。";
            if(a !== null){
              // 显示中
              alert1_show_status = 1;
              a.className = "z-50 relative";
              // 3s后自动隐藏alert1
              alert_timer = setTimeout(() => {
                var a = document.getElementById("alert1");
                if (a != null){
                  a.className = 'hidden';
                  //显示结束
                  alert1_show_status = 2;
                }
              }, 3000);
              //console.log('已创建临时定时器'+alert_timer.toString())
              //console.log('定时器(from_save_character2)'+temp_interval.toString()+'已清除')
              clearInterval(temp_interval);
            }   
          }, 10)    

        const data = await response.json();
        assistant_profile_changed = true;
        console.log('File uploaded successfully:', data);
      } else {
        const data = await response.json();
        if (data.error === 'File too large'){
          alert('文件太大了！');
        }
        else{
          alert(data.error);
        }
        console.error('File upload failed');
      }
    } catch (error) {
      alert(error);
      console.error('Error uploading file:', error);
    }
  };  

  if (type === 0){
    return(
      <div id='history_content' className='invisible overflow-y-auto'>

        {
          msgs.map((item) => {
            if (messages[item.index] !== undefined){
              if(messages[item.index]['role'] === 'user'){
                return(
                  <MainInfoUserMsg key={item.temp_id} data={item} imageUrl={imageUrl2}></MainInfoUserMsg>            
                )
              }
              else{
                return(
                  <MainInfoAssistantMsg key={item.temp_id} data={item} imageUrl={imageUrl1}></MainInfoAssistantMsg>  
                )              
              }
            }
          })
        }

      </div>
    );   
  }

  if (type === -1 || type === 1){
    return(
      <textarea id="main-info" readOnly disabled style={{height:'calc(100% - 2rem)',min_height:'6rem'}} className="ml-2 mt-4 max-h-full outline-0">
      </textarea>
    )
  }
  if (type === 2){
    return(
      <div className='relative overflow-y-auto'>
        <textarea id="main-info" style={{height:'calc(100% - 2rem)',min_height:'6rem',width:'calc(100% - 0.5rem)'}} className="ml-2 mt-4 max-h-full outline-0">        
        </textarea>
        <button
          id='save3'
          disabled={button3Disabled}
          className={!mouseDown ? 'absolute bottom-4 right-4 h-10 w-16 rounded-lg bg-gray-200 grid place-content-center font-bold hover:bg-gray-300 disabled:cursor-not-allowed' : 'absolute bottom-4 right-4 h-10 w-16 rounded-lg bg-gray-400 grid place-content-center font-bold'}
          onClick={save_character2}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
          >
          保存
        </button>
      </div>
    )
  }
  if (type === 3){
    return(
      //main-info2和main-info3的className要不同，否则它们互相转换时无法被正确设置为invisible
      <div id="main-info2" className='invisible ml-3'>
        <div className='mt-4'>
          <label htmlFor="model">
            <span className="ml-2 text-xl font-bold text-gray-700"> 模型(聊天) </span>
          </label>      
        </div>
        <div className='mt-4'>
            <select
              name="model"
              id="model"
              style={{width:'calc(100% - 1rem)'}}
              className="h-10 ml-2 mt-0.5 rounded border-gray-300 shadow-sm focus:outline-0"
            >
              <option value="model1">deepseek-chat</option>
              <option value="model2">deepseek-reasoner</option>
            </select>
        </div>
        <div className="mt-4">
          <label htmlFor="api_key">
            <span className="ml-2 text-xl font-bold text-gray-700"> API key</span>
          </label>
        </div>
        <div className='mt-4'>
            <input
              type="api_key"
              id="api_key"
              style={{width:'calc(100% - 1rem)'}}
              className="pl-1 pr-1 h-10 ml-2 mt-0.5 rounded border-gray-300 shadow-sm focus:outline-0"
            />          
        </div>
        <div className='mt-4'>
          <label htmlFor="model2">
            <span className="ml-2 text-xl font-bold text-gray-700"> 模型2(从对话中提取重要信息) </span>
          </label>      
        </div>
        <div className='mt-4'>
            <select
              name="model2"
              id="model2"
              style={{width:'calc(100% - 1rem)'}}
              className="h-10 ml-2 mt-0.5 rounded border-gray-300 shadow-sm focus:outline-0"
            >
              <option value="model1">deepseek-chat</option>
              <option value="model2">deepseek-reasoner</option>
            </select>
        </div>
        <div className="mt-4">
          <label htmlFor="api_key2">
            <span className="ml-2 text-xl font-bold text-gray-700"> API key2</span>
          </label>
        </div>
        <div className='mt-4'>
            <input
              type="api_key2"
              id="api_key2"
              style={{width:'calc(100% - 1rem)'}}
              className="pl-1 pr-1 h-10 ml-2 mt-0.5 rounded border-gray-300 shadow-sm focus:outline-0"
            />          
        </div> 
        <div className="mt-4">
          <label htmlFor="api_key3">
            <span className="ml-2 text-xl font-bold text-gray-700"> API key3(硅基流动:RAG模型)</span>
          </label>
        </div>
        <div className='mt-4'>
            <input
              type="api_key3"
              id="api_key3"
              style={{width:'calc(100% - 1rem)'}}
              className="pl-1 pr-1 h-10 ml-2 mt-0.5 rounded border-gray-300 shadow-sm focus:outline-0"
            />          
        </div>                 
        <button
          id='save'
          disabled={buttonDisabled}
          className={!mouseDown ? 'absolute bottom-4 right-4 h-10 w-16 rounded-lg bg-gray-200 grid place-content-center font-bold hover:bg-gray-300 disabled:cursor-not-allowed' : 'absolute bottom-4 right-4 h-10 w-16 rounded-lg bg-gray-400 grid place-content-center font-bold'}
          onClick={save_changes}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
          >
          保存
        </button>        
      </div>          
    )    
  }
  if (type === 4){
    return(
      <div id="main-info3" className='invisible ml-4'>
        <div className="mt-4">
          <label htmlFor="user_name">
            <span className="ml-2 text-xl font-bold text-gray-700">你在聊天中的昵称</span>
          </label>
        </div>
        <div className='mt-4'>
            <input
              type="user_name"
              id="user_name"
              style={{width:'calc(100% - 1rem)'}}
              className="pl-1 pr-1 h-10 ml-2 mt-0.5 rounded border-gray-300 shadow-sm focus:outline-0"
            />          
        </div>
        <div className="mt-4">
          <label htmlFor="assistant_name">
            <span className="ml-2 text-xl font-bold text-gray-700">助理的昵称</span>
          </label>
        </div>
        <div className='mt-4'>
            <input
              type="assistant_name"
              id="assistant_name"
              style={{width:'calc(100% - 1rem)'}}
              className="pl-1 pr-1 h-10 ml-2 mt-0.5 rounded border-gray-300 shadow-sm focus:outline-0"
            />          
        </div>
        <div className="mt-4">
          <label htmlFor="assistant_name">
            <span className="ml-2 text-xl font-bold text-gray-700">你的头像</span>
          </label>
        </div>
        <div className="mt-4">
          <label htmlFor="file" style={{width:'calc(100% - 1rem)'}} className="ml-2 block rounded border-gray-300 p-4 text-gray-900 shadow-sm">
            <div className="flex items-center justify-center gap-4">
              <span className="font-medium">{file !== null ? file.name : 'Upload your file here:D'}</span>

              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                className="size-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M7.5 7.5h-.75A2.25 2.25 0 0 0 4.5 9.75v7.5a2.25 2.25 0 0 0 2.25 2.25h7.5a2.25 2.25 0 0 0 2.25-2.25v-7.5a2.25 2.25 0 0 0-2.25-2.25h-.75m0-3-3-3m0 0-3 3m3-3v11.25m6-2.25h.75a2.25 2.25 0 0 1 2.25 2.25v7.5a2.25 2.25 0 0 1-2.25 2.25h-7.5a2.25 2.25 0 0 1-2.25-2.25v-.75"
                />
              </svg>
              <button
                disabled={button4Disabled}
                onClick={handleUpload1}
                onMouseDown={handleMouseDown2}
                onMouseUp={handleMouseUp2}
                onMouseLeave={handleMouseLeave2}
                className={!mouseDown2 ? 'pl-2 pr-2 h-10 rounded-lg bg-gray-200 font-bold hover:bg-gray-300 disabled:cursor-not-allowed' : 'pl-2 pr-2 h-10 rounded-lg bg-gray-400 font-bold'}
              >
                确认上传
              </button>
            </div>

            <input
              type="file"
              id="file"
              onChange={handleFileChange}
              className="sr-only" />
          </label>          
        </div>
        <div className="mt-4">
          <label htmlFor="assistant_name">
            <span className="ml-2 text-xl font-bold text-gray-700">助理的头像</span>
          </label>
        </div>
        <div className="mt-4">
          <label htmlFor="file2" style={{width:'calc(100% - 1rem)'}} className="ml-2 block rounded border-gray-300 p-4 text-gray-900 shadow-sm">
            <div className="flex items-center justify-center gap-4">
              <span className="font-medium">{file2 !== null ? file2.name : 'Upload your file here:D'}</span>

              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                className="size-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M7.5 7.5h-.75A2.25 2.25 0 0 0 4.5 9.75v7.5a2.25 2.25 0 0 0 2.25 2.25h7.5a2.25 2.25 0 0 0 2.25-2.25v-7.5a2.25 2.25 0 0 0-2.25-2.25h-.75m0-3-3-3m0 0-3 3m3-3v11.25m6-2.25h.75a2.25 2.25 0 0 1 2.25 2.25v7.5a2.25 2.25 0 0 1-2.25 2.25h-7.5a2.25 2.25 0 0 1-2.25-2.25v-.75"
                />
              </svg>
              <button
                disabled={button5Disabled}
                onClick={handleUpload2}
                onMouseDown={handleMouseDown3}
                onMouseUp={handleMouseUp3}
                onMouseLeave={handleMouseLeave3}
                className={!mouseDown3 ? 'pl-2 pr-2 h-10 rounded-lg bg-gray-200 font-bold hover:bg-gray-300 disabled:cursor-not-allowed' : 'pl-2 pr-2 h-10 rounded-lg bg-gray-400 font-bold'}
              >
                确认上传
              </button>
            </div>

            <input
              type="file"
              id="file2"
              onChange={handleFileChange2}
              className="sr-only" />
          </label>          
        </div>                                
        <button
          id='save2'
          disabled={button2Disabled}
          className={!mouseDown ? 'absolute bottom-4 right-4 h-10 w-16 rounded-lg bg-gray-200 grid place-content-center font-bold hover:bg-gray-300 disabled:cursor-not-allowed' : 'absolute bottom-4 right-4 h-10 w-16 rounded-lg bg-gray-400 grid place-content-center font-bold'}
          onClick={save_others}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
          >
          保存
        </button>        
      </div>        
    )
  }
}

function SaveAlert(){

  function handleClick(){
    var a = document.getElementById("alert1");
    if (a != null){
      a.className='hidden';
    }
  }

  return(
    <div id="alert1" className='hidden'>
      <div role="alert" className="absolute left-1/2 top-48 -ml-48 w-96 rounded-md border border-gray-300 bg-white p-4 shadow-sm">
        <div className="flex items-start gap-4">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="1.5"
            stroke="currentColor"
            className="size-6 text-green-600"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>

          <div className="flex-1">
            <strong id="alert1_s1" className="font-medium text-gray-900"></strong>

            <p id="alert1_s2" className="mt-0.5 text-sm text-gray-700"></p>
          </div>

          <button
            className="-m-3 rounded-full p-1.5 text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700"
            type="button"
            onClick={handleClick}
            aria-label="Dismiss alert"
          >
            <span className="sr-only">Dismiss popup</span>

            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
              stroke="currentColor"
              className="size-5"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>  
    </div>  
  )
}

function SendArea(){
  const [mouseDown, setMouseDown] = useState(false);
  const [buttonDisabled, setButtonDisabled] = useState(false);

  function send_message(){
    if (selected_type === 0){
      var s = document.getElementById("send_area");
      var msg = s.value;
      if (msg.length > 0){
        messages.push({"role":"user","content":msg});
        is_history_msgs = false ;

        socket.emit('get_api_response', messages[messages.length - 1]["content"]);
        if (!get_onetime_response){
          get_onetime_response = true;
          socket.once('merge_result', function(msg) {
            messages.push({"role":"assistant","content":'please wait patiently...'});
            is_history_msgs = false;
            setButtonDisabled(true);
            socket.off('merge_result');

            var second = 0;

            //持续更新等待状态
            var temp_interval = setInterval(() => {
              if (get_onetime_response){
                second += 1;
                messages[messages.length - 1]["content"] = 'please wait patiently...(' + second.toString()+'s)';

                var m = document.getElementById('msg'+(messages.length - 1).toString());
                m.innerHTML = messages[messages.length - 1]["content"];
              }
              else{
                clearInterval(temp_interval);
              }
            }, 1000);
          });
          socket.once('final_response', function(msg) {
            setButtonDisabled(false);
            get_onetime_response = false;
            messages[messages.length - 1]["content"] = msg;
            var m = document.getElementById('msg'+(messages.length - 1).toString());
            if (m != null){
              m.innerHTML = messages[messages.length - 1]["content"];
            }
            
              var i2 = setInterval(() => {
                var h = document.getElementById("history_content");
                if(h !== null){
                  //滚动到底部
                  h.scrollTop = h.scrollHeight;
                  h.className = 'visible overflow-y-auto';
                  //console.log('定时器(from_useEffect_i2)'+i2.toString()+'已清除')
                  clearInterval(i2);                    
                }
              },10)            
            //错误监听
            var temp_timer = setTimeout(() => {
              socket.off('error');
            }, 30000);
            
            //console.log('已创建临时定时器'+temp_timer.toString())

            socket.once('error',function(msg){               
              if (msg.length > 0){
                messages.push({"role":"assistant","content":'Oops! An error has occurred! Please try to send a message again!'}); 
                is_history_msgs = false;
              }

              var i2 = setInterval(() => {
                var h = document.getElementById("history_content");
                if(h !== null){
                  //滚动到底部
                  h.scrollTop = h.scrollHeight;
                  h.className = 'visible overflow-y-auto';
                  //console.log('定时器(from_useEffect_i2)'+i2.toString()+'已清除')
                  clearInterval(i2);                    
                }
              },10)    
            });
          });             
        } 

        //清空发送内容
        s.value = "";
      }
    }
    else{
      console.log('当前不处于聊天界面，发送消息失败!');
    }
  }

  function handleMouseDown(){
    setMouseDown(true);
  }

  function handleMouseUp(){
    setMouseDown(false);
  }

  function handleMouseLeave(){
    setMouseDown(false);
  }

  return(
    <div className='relative'>
      <div className="mt-2 h-32 rounded-lg bg-gray-50 grid">
        <textarea style={{height:'100% - 1.5rem'}} id='send_area' className="mt-2 ml-2 grid place-content-center rounded-lg outline-0"></textarea>
      </div>
      <button
          id='save'
          disabled={buttonDisabled}
          className={!mouseDown ? 'absolute bottom-4 right-4 h-10 w-16 rounded-lg bg-gray-200 grid place-content-center font-bold hover:bg-gray-300 disabled:cursor-not-allowed' : 'absolute bottom-4 right-4 h-10 w-16 rounded-lg bg-gray-400 grid place-content-center font-bold'}
          onClick={send_message}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
          >
          发送
        </button>   
    </div>
  )
}

function App() {
  const[current_selected_type, set_current_selected_type] = useState(0);

  // 使用回调函数将子组件的参数传递给父组件
  function change_selected_type(type){
    set_current_selected_type(type);
  }

  return (
    <div>
      <SaveAlert></SaveAlert>
      <div className="h-screen min-h-96 min-w-64 flex gap-2">
        <div className="ml-2 mt-2 gap-2 rounded-lg">
          <BLeft callback_func={change_selected_type}></BLeft>    
        </div>
        <div style={{height:'calc(100% - 1rem)'}} className="mt-2 mr-2 w-screen gap-2 rounded-lg">
          <div id="main1" style={{height:'calc(100% - 8.5rem)'}} className={current_selected_type === 0 ? "min-h-96 pt-4 pb-4 rounded-lg bg-gray-50 grid" : "min-h-96 rounded-lg bg-gray-50 grid"}>
            {/* <MainInfo></MainInfo> */}
            {MainInfo(current_selected_type)}
          </div>
          <SendArea></SendArea>
        </div>
      </div>
    </div>
  );
}

export default App;
