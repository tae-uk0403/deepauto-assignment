# Deepauto-Assignment

## Getting Started

### Dependencies

- **OS**: macOS
- **Python**: Python 3.10
- **Kubernetes cluster**: minikube

Python library:
- `kubernetes` - Kubernetes Python 클라이언트 라이브러리





## Task 1
`hello_kube.py` 스크립트는 Kubernetes API를 사용하여 "hello"라는 이름의 Pod를 생성하고, 생성 완료 후 Pod의 로그를 출력하고, 자동으로 Pod를 삭제합니다. 

주요 기능 및 실행 순서:

1. **`create_pod(core_api, name, namespace)`**: hello라는 이름의 Pod 생성
2. **`check_pod_completion(core_api, name, namespace)`**: Pod가 완료 상태가 되면, Pod의 로그를 출력한 후 Pod를 삭제합니다.
