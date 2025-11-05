import time, os
from kubernetes import client, config
from kubernetes.client.rest import ApiException

NAME = "hello"  # 생성할 Pod의 이름
NS = "demo"  # 사용할 namespace



def create_pod(core_api, name, namespace):
    """ pod 생성 """
    pod_manifest = client.V1Pod(
        metadata=client.V1ObjectMeta(name=name),
        spec=client.V1PodSpec(
            containers=[client.V1Container(
                name="c", image="busybox",
                command=["/bin/sh", "-c", "echo hello world"]
            )],
            restart_policy="Never"
        )
    )
    core_api.create_namespaced_pod(namespace=namespace, body=pod_manifest)


def check_pod_completion(core_api, name, namespace):
    """ pod 생성 완료 체크 및 로그 출력 후 pod 삭제 """
    while True:
        p = core_api.read_namespaced_pod(name, namespace)
        phase = (p.status.phase or "")
        
        # 생성 완료되었다면 log 출력 및 pod 삭제
        if phase in ("Succeeded", "Failed"):
            print(core_api.read_namespaced_pod_log(name, namespace))
            core_api.delete_namespaced_pod(name, namespace)
            return

def main():

    kcfg = os.environ.get("KUBECONFIG")
    if not kcfg:
        raise RuntimeError("KUBECONFIG not set")
    config.load_kube_config(config_file=kcfg)
    core = client.CoreV1Api()

    # Kubernetes API에 연결 설정
    config.load_kube_config()
    core = client.CoreV1Api()
    
    # Pod 생성
    create_pod(core, NAME, NS)
    
    # pod 생성 완료 체크
    check_pod_completion(core, NAME, NS)



if __name__ == "__main__":
    main()
