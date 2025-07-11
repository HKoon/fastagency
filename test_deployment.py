#!/usr/bin/env python3
"""
部署测试脚本

用于测试 FastAgency 在 Railway 上的部署是否正常工作
"""

import os
import sys
import asyncio
import httpx
import json
from typing import Dict, Any

# 测试配置
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
TIMEOUT = 30.0

class DeploymentTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.results = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_result(self, test_name: str, success: bool, message: str, data: Any = None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "data": data
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if data and not success:
            print(f"   详细信息: {data}")
    
    async def test_health_check(self):
        """测试健康检查端点"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_result("健康检查", True, "应用运行正常", data)
                else:
                    self.log_result("健康检查", False, "应用状态异常", data)
            else:
                self.log_result("健康检查", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("健康检查", False, f"请求失败: {str(e)}")
    
    async def test_database_status(self):
        """测试数据库连接状态"""
        try:
            response = await self.client.get(f"{self.base_url}/db/status")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("database_connected"):
                    self.log_result("数据库连接", True, "数据库连接正常", data)
                else:
                    self.log_result("数据库连接", False, "数据库连接失败", data)
            else:
                self.log_result("数据库连接", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("数据库连接", False, f"请求失败: {str(e)}")
    
    async def test_config_endpoint(self):
        """测试配置信息端点"""
        try:
            response = await self.client.get(f"{self.base_url}/config")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["openai_model", "version"]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("配置信息", True, "配置信息完整", data)
                else:
                    self.log_result("配置信息", False, f"缺少字段: {missing_fields}", data)
            else:
                self.log_result("配置信息", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("配置信息", False, f"请求失败: {str(e)}")
    
    async def test_workflows_list(self):
        """测试工作流列表端点"""
        try:
            response = await self.client.get(f"{self.base_url}/workflows")
            
            if response.status_code == 200:
                data = response.json()
                workflows = data.get("workflows", [])
                
                if len(workflows) > 0:
                    workflow_names = [wf["name"] for wf in workflows]
                    self.log_result("工作流列表", True, f"发现 {len(workflows)} 个工作流: {workflow_names}", data)
                else:
                    self.log_result("工作流列表", False, "未发现任何工作流", data)
            else:
                self.log_result("工作流列表", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("工作流列表", False, f"请求失败: {str(e)}")
    
    async def test_chat_workflow(self):
        """测试聊天工作流"""
        try:
            payload = {
                "message": "Hello, this is a test message."
            }
            
            response = await self.client.post(
                f"{self.base_url}/workflows/chat_assistant",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data or "response" in data or "summary" in data:
                    self.log_result("聊天工作流", True, "工作流执行成功", {"response_keys": list(data.keys())})
                else:
                    self.log_result("聊天工作流", False, "响应格式异常", data)
            else:
                self.log_result("聊天工作流", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("聊天工作流", False, f"请求失败: {str(e)}")
    
    async def test_learning_workflow(self):
        """测试学习工作流"""
        try:
            payload = {
                "message": "I want to learn about Python programming.",
                "max_rounds": 2
            }
            
            response = await self.client.post(
                f"{self.base_url}/workflows/simple_learning",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data or "response" in data or "summary" in data:
                    self.log_result("学习工作流", True, "工作流执行成功", {"response_keys": list(data.keys())})
                else:
                    self.log_result("学习工作流", False, "响应格式异常", data)
            else:
                self.log_result("学习工作流", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("学习工作流", False, f"请求失败: {str(e)}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print(f"🚀 开始测试 FastAgency 部署: {self.base_url}")
        print("=" * 60)
        
        # 基础功能测试
        await self.test_health_check()
        await self.test_config_endpoint()
        await self.test_workflows_list()
        
        # 数据库测试
        await self.test_database_status()
        
        # 工作流测试
        await self.test_chat_workflow()
        await self.test_learning_workflow()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        # 保存详细报告到文件
        report_data = {
            "base_url": self.base_url,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.results
        }
        
        with open("deployment_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 详细报告已保存到: deployment_test_report.json")
        
        return failed_tests == 0

async def main():
    """主函数"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL
    
    print(f"🔍 测试目标: {base_url}")
    
    async with DeploymentTester(base_url) as tester:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 所有测试通过！部署成功！")
            sys.exit(0)
        else:
            print("\n⚠️  部分测试失败，请检查部署配置")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())