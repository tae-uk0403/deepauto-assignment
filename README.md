# Deepauto-Assignment

## Getting Started

### Dependencies

- **OS**: macOS
- **Python**: Python 3.10
- **Kubernetes cluster**: minikube

Python library:
- `kubernetes` - Kubernetes Python 클라이언트 라이브러리





## Task 1
`hello_kube.py` 스크립트는 Kubernetes API를 사용하여 "hello"라는 이름의 Pod를 생성하고, 생성 완료 후 Pod의 로그를 출력하고, 자동으로 Pod를 삭제

주요 기능 및 실행 순서:

1. **`create_pod(core_api, name, namespace)`**: hello라는 이름의 Pod 생성
2. **`check_pod_completion(core_api, name, namespace)`**: Pod가 완료 상태가 되면, Pod의 로그를 출력한 후 Pod를 삭제

## Task 2
Kubernetes 클러스터에 GitHub Actions Runner Controller (ARC)를 배포

참고 - https://github.com/actions/actions-runner-controller/blob/master/docs/quickstart.md


## Task 3

GitHub Actions에서 OIDC 인증을 통해 Kubernetes API에 접근하는 기능을 구현했습니다.

GitHub Actions에서 발급받은 OIDC 토큰을 사용하여 Kubernetes API에서 pod 목록을 조회하고, 인증과 권한 부여가 정상적으로 작동하는지 확인했습니다.

### 전체 단계

1. Kubernetes API 서버 OIDC 설정 (클러스터 측)
2. Kubernetes RBAC 권한 설정 (Role, RoleBinding 생성)
3. GitHub Actions 워크플로우 설정 (OIDC 토큰 요청 및 사용)

### 단계 1: Kubernetes API 서버에 GitHub Actions OIDC 신뢰 설정

Minikube 시작 시 `--extra-config` 옵션으로 API 서버 플래그 추가:

```bash
minikube start \
  --extra-config=apiserver.oidc-issuer-url="https://token.actions.githubusercontent.com" \
  --extra-config=apiserver.oidc-client-id="kubernetes" \
  --extra-config=apiserver.oidc-username-claim="sub" \
  --extra-config=apiserver.oidc-username-prefix="github-actions:" \
  --extra-config=apiserver.oidc-required-claim="repository=ntw0403/deepauto_assignment"
```

설정 옵션 설명:
- `oidc-issuer-url`: GitHub Actions OIDC 발급자 URL (고정값)
- `oidc-client-id`: 클러스터 식별자 (임의로 지정, 예: kubernetes)
- `oidc-username-claim`: 토큰에서 사용자명 추출 필드 (sub 사용)
- `oidc-username-prefix`: 사용자명 앞에 붙을 접두사 (github-actions:)
- `oidc-required-claim`: 접근 허용할 리포지토리 제한 (보안 강화)

### 단계 2: Kubernetes RBAC 권한 설정

OIDC 토큰으로 인증된 사용자에게 필요한 최소 권한 부여

#### 2-1. Namespace 생성

```bash
kubectl create namespace demo
```

#### 2-2. Role 생성

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: demo
  name: actions-oidc-role
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list", "create", "update", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "watch", "list", "create", "update", "delete"]
```

#### 2-3. RoleBinding 생성

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: actions-oidc-binding
  namespace: demo
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: actions-oidc-role
subjects:
- kind: User
  name: github-actions:repo:ntw0403/deepauto_assignment
```

### 단계 3: GitHub Actions 워크플로우 설정

#### 3-1. API 서버 정보 수집

```bash
# API 서버 주소
kubectl cluster-info
# 출력 예: https://192.168.49.2:8443

# CA 인증서 데이터 (base64 인코딩)
kubectl config view --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}'
```

#### 3-2. Composite Action 생성

`.github/actions/k8s-set-context-with-id-token/action.yaml` 파일 생성:

```yaml
# composite action 내부의 핵심 스텝(신입 스타일)
- name: Mask token
  shell: bash
  run: |
    echo "::add-mask::${{ inputs.token }}"

- name: Write kubeconfig
  shell: bash
  env:
    KCFG: ${{ github.workspace }}/kubernetes-kubeconfig
  run: |
    # kubeconfig 파일이 있으면 삭제함 (명시적으로 확인)
    if [ -f "$KCFG" ]; then
      rm "$KCFG"
    fi

    # cluster 정보 설정
    kubectl config --kubeconfig="$KCFG" set-cluster kubernetes \
      --server="${{ inputs.server }}" \
      --certificate-authority-data="${{ inputs.certificate-authority-data }}"

    # 사용자(토큰) 설정
    kubectl config --kubeconfig="$KCFG" set-credentials github-actions \
      --token="${{ inputs.token }}"

    # 컨텍스트와 기본 네임스페이스 설정
    kubectl config --kubeconfig="$KCFG" set-context github-actions \
      --cluster=kubernetes --user=github-actions --namespace="${{ inputs.namespace }}"

    # 컨텍스트 활성화 및 KUBECONFIG export
    kubectl config --kubeconfig="$KCFG" use-context github-actions
    echo "KUBECONFIG=$KCFG" >> "$GITHUB_ENV"
```

#### 3-3. 워크플로우 파일 생성
.github/workflows/deploy-kubernetes.yaml 파일 생성:

```yaml
name: deploy-kubernetes
permissions:
  id-token: write
  contents: read

on:
  push:
    branches: ["main"]
  workflow_dispatch:

jobs:
  oidc-demo:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4

      - name: Create OIDC token
        id: create-oidc-token
        uses: actions/github-script@v7
        with:
          script: |
            const t = await core.getIDToken('kubernetes')   // 반드시 kube-apiserver의 --oidc-client-id 와 동일해야 함
            core.setOutput('id_token', t)

      - name: Create kubeconfig (use token)
        env:
          KCFG: ${{ github.workspace }}/kubeconfig
        run: |
          cat > "$KCFG" <<'EOF'
          apiVersion: v1
          kind: Config
          clusters:
          - name: kubernetes
            cluster:
              server: ${{ secrets.K8S_SERVER }}
              certificate-authority-data: ${{ secrets.K8S_CA_DATA }}
          users:
          - name: github-actions
            user:
              token: ${{ steps.create-oidc-token.outputs.id_token }}
          contexts:
          - name: github-actions
            context:
              cluster: kubernetes
              user: github-actions
              namespace: demo
          current-context: github-actions
          EOF
          echo "KUBECONFIG=$KCFG" >> $GITHUB_ENV

      - name: Run hello_kube
        env:
          NAMESPACE: demo
        run: python3 hello_kube.py 'echo hiii && sleep 1'
```
