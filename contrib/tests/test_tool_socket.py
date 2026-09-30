#!/usr/bin/env python3
"""Actual ToolSocket method bodies, real MessageBuffer/JsonCpp, ASan and UBSan."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/game/Server/ToolSocket.cpp').read_text('utf8')
    def extract(name):
        return re.search(r'^(?:bool|void) '+re.escape(name)+r'\([^\n]*\)\n\{.*?^\}',source,re.M|re.S)[0]
    names=['ProcessCmd','ProcessToolCmd','ReadHandler','SendResult','SendPacket']
    handlers=['Heartbeat','Authorization','BGXPReward','BGScoreRate','CreateAccount','PlayerAccount',
              'AccountSecurity','PlayerChange','PVEMaxLevel','PVEMaxDungeon','PVEAddion']
    harness=r'''
#include "MessageBuffer.h"
#include "json.h"
#include <queue>
#include <mutex>
#include <string>
#include <limits>
#include <cmath>
#include <stdexcept>
#include <iostream>
#define TC_LOG_ERROR(...) ((void)0)
#define MAX_SPECIALIZATIONS 4
#define PLAYER_SPECIALIZATION_KEEP 255
void check(bool ok,char const* message){if(!ok)throw std::runtime_error(message);}
struct ToolSocket {
    bool _authed=true,open=true;
    MessageBuffer input;
    std::queue<MessageBuffer> _bufferQueue;
    std::queue<Json::Value> _processCmd;
    std::mutex _commandLock;
    unsigned reads=0,handled=0,rejected=0;
    bool IsOpen() const{return open;}
    void DelayedCloseSocket(){open=false;}
    MessageBuffer& GetReadBuffer(){return input;}
    void AsyncRead(){++reads;}
    void SendNormalResult(std::string const&,bool ok){if(!ok)++rejected;}
    void Handle(Json::Value& info){++handled;if(info["throw"].asBool())throw std::runtime_error("fixture failure");}
    void ProcessCmd(std::string);
    void ProcessToolCmd();
    void ReadHandler();
    void SendResult(std::string);
    void SendPacket(MessageBuffer&&);
'''
    harness+='\n'.join('    void Cmd'+h+'(Json::Value& v){Handle(v);}' for h in handlers)
    harness+='\n};\n'+extract('IsValidToolCommand')+'\n'
    harness+='\n'.join(extract('ToolSocket::'+name) for name in names)
    harness+=r'''
std::string frame(std::string payload,bool nul=true){
    if(nul)payload.push_back('\0');
    uint16 size=static_cast<uint16>(payload.size());
    std::string out(reinterpret_cast<char*>(&size),sizeof(size));return out+payload;
}
void feed(ToolSocket& socket,std::string const& bytes){
    socket.input.Normalize();
    if(socket.input.GetRemainingSpace()<bytes.size())socket.input.Resize(socket.input.GetActiveSize()+bytes.size());
    socket.input.Write(bytes.data(),bytes.size());socket.ReadHandler();
}
int main(){
    std::string message="{\"entry\":\"heartbeat\"}";
    auto wire=frame(message);
    for(std::size_t split=1;split<wire.size();++split){
        ToolSocket socket;feed(socket,wire.substr(0,split));
        check(socket._processCmd.empty(),"partial frame executed");
        feed(socket,wire.substr(split));socket.ProcessToolCmd();
        check(socket.handled==1 && socket.open && socket.input.GetActiveSize()==0,"fragment recovery");
    }
    ToolSocket joined;feed(joined,frame(message)+frame(message,false));joined.ProcessToolCmd();
    check(joined.handled==2,"coalesced frames / no NUL");
    ToolSocket zero;feed(zero,std::string(2,'\0')+wire);zero.ProcessToolCmd();check(zero.handled==1,"zero-length frame");
    ToolSocket oversized;uint16 bad=1025;feed(oversized,std::string(reinterpret_cast<char*>(&bad),2));
    check(!oversized.open && oversized._processCmd.empty(),"oversized request accepted");
    ToolSocket embedded;feed(embedded,frame(message+std::string(1,'\0')+"junk"));check(!embedded.open,"embedded NUL accepted");
    ToolSocket malformed;feed(malformed,frame("not json")+wire);malformed.ProcessToolCmd();
    check(malformed.handled==1,"malformed JSON stops following command");
    ToolSocket invalid;
    for(char const* json:{"null","[]","42","{\"entry\":[]} ",
        "{\"entry\":\"player_change\",\"guid\":1,\"minlv\":20,\"maxlv\":110,\"talent\":\"3\"}",
        "{\"entry\":\"set_security\",\"accid\":1,\"security\":5}",
        "{\"entry\":\"player_change\",\"guid\":4294967295,\"minlv\":20,\"maxlv\":110}",
        "{\"entry\":\"bg_scorerate\",\"scorerate\":true}",
        "{\"entry\":\"create_acc\",\"cmdName\":[],\"cmdPass\":\"secret\"}"})invalid.ProcessCmd(json);
    invalid.ProcessToolCmd();check(invalid.handled==0 && invalid.rejected==9,"invalid schema dispatched");
    ToolSocket valid;
    for(char const* json:{"{\"entry\":\"player_change\",\"guid\":1,\"minlv\":20,\"maxlv\":110}",
        "{\"entry\":\"player_change\",\"guid\":1,\"minlv\":20,\"maxlv\":110,\"talent\":255}",
        "{\"entry\":\"player_change\",\"guid\":1,\"minlv\":20,\"maxlv\":110,\"talent\":3}",
        "{\"entry\":\"xp_reward\",\"reward\":1}","{\"entry\":\"xp_reward\",\"reward\":false}"})valid.ProcessCmd(json);
    valid.ProcessToolCmd();check(valid.handled==5 && valid.rejected==0,"compatible request rejected");
    ToolSocket exceptions;exceptions.ProcessCmd("{\"entry\":\"heartbeat\",\"throw\":true}");exceptions.ProcessCmd(message);
    exceptions.ProcessToolCmd();check(exceptions.handled==2 && exceptions.rejected==1,"exception prevents next command");
    for(std::size_t length:{1u,100u,65534u}){
        ToolSocket reply;std::string payload(length,'x');reply.SendResult(payload);
        check(reply._bufferQueue.size()==1,"reply not queued");
        MessageBuffer const& buffer=reply._bufferQueue.front();
        check(buffer.GetActiveSize()==length+3 && buffer.GetActiveSize()==buffer.GetBufferSize(),"reply length exceeds storage");
        auto& b=reply._bufferQueue.front();uint16 size=0;memcpy(&size,b.GetReadPointer(),2);
        check(size==length+1 && b.GetReadPointer()[length+2]==0,"wire size/NUL changed");
    }
    ToolSocket tooLarge;tooLarge.SendResult(std::string(65535,'x'));
    check(!tooLarge.open && tooLarge._bufferQueue.empty(),"response length wrapped");
    ToolSocket closed;closed.open=false;closed.SendResult("ignored");check(closed._bufferQueue.empty(),"closed queue");
    std::cout<<"PASS: fragmented/coalesced frames, bounds, JSON validation, recovery, reply length\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);cpp=tmp/'tool.cpp';exe=tmp/'tool'
        (tmp/'Define.h').write_text('#pragma once\n#include <cstdint>\nusing uint8=std::uint8_t; using uint16=std::uint16_t;\n',encoding='utf8')
        cpp.write_text(harness,encoding='utf8')
        json=root/'src/server/game/Server/Json'
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-fsanitize=address,undefined','-fno-omit-frame-pointer','-g',
            '-I'+str(tmp),'-I'+str(root/'src/common/Utilities'),'-I'+str(json),str(cpp),
            *[str(json/f) for f in ('json_reader.cpp','json_value.cpp','json_writer.cpp')],'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
