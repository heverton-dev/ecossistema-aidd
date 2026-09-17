# Múltiplas contas do Antigravity no Orca ADE (via WSL + SSH)

## Objetivo

O Orca não tem um "trocador de contas" para o Antigravity como tem para Claude e Codex — ele só lê a credencial que o `agy` (CLI do Antigravity) já tem logada localmente. Este manual mostra como contornar isso: usar uma distro WSL como um "host" separado, com o Antigravity logado numa segunda conta do Google, e cadastrar esse host como **SSH Target** no Orca. Assim é possível ter uma conta do Antigravity no Windows e outra(s) dentro do WSL, cada uma usada em worktrees diferentes.

Esse é o único caminho confirmado pela própria equipe do Orca (via PR de leitura de cota do Antigravity "including SSH hosts") — não existe integração nativa de múltiplas contas do Antigravity dentro do Orca.

## Pré-requisitos

- Windows 10 (build recente) ou Windows 11.
- PowerShell com permissão de Administrador.
- Uma segunda conta Google que você quer usar no Antigravity.

## Fase 0 — Verificar se o WSL já está instalado

Abra o **PowerShell** (não precisa ser Admin para este comando) e rode:

```powershell
wsl -l -v
```

- Se der erro tipo "comando não reconhecido" ou "recurso não instalado" → siga o **Caminho A (WSL do zero)**.
- Se listar uma ou mais distros (ex: `Ubuntu`) → siga o **Caminho B (WSL já instalado)**.

---

## Caminho A — WSL não está instalado (instalação do zero)

### A.1 — Instalar o WSL

No **PowerShell como Administrador**:

```powershell
wsl --install
```

Isso instala o WSL2 com Ubuntu como distro padrão. **Reinicie o computador** quando for pedido.

### A.2 — Configurar o usuário do Ubuntu

Após reiniciar, o Ubuntu abre sozinho (ou procure "Ubuntu" no menu Iniciar). Na primeira execução, ele pede:

```
Enter new UNIX username: (escolha um nome, ex: seuusuario)
New password: (digite uma senha)
Retype new password: (repita a senha)
```

Guarde esse usuário e senha — vai usar nas próximas fases.

Depois disso, vá direto para a **Fase 1 (comum aos dois caminhos)**.

---

## Caminho B — WSL já está instalado

Como já existe uma distro, crie uma **nova e separada**, dedicada só a essa segunda conta do Antigravity — isso evita misturar com o que você já usa no WSL.

### B.1 — Criar uma distro nova com nome próprio

No **PowerShell como Administrador**:

```powershell
wsl --install Ubuntu --name Antigravity2
```

Isso instala uma segunda cópia do Ubuntu, chamada `Antigravity2`, sem mexer na distro que já existia.

### B.2 — Configurar o usuário dessa nova distro

Abra a distro nova:

```powershell
wsl -d Antigravity2
```

Na primeira execução, ela pede:

```
Enter new UNIX username: (escolha um nome, ex: seuusuario)
New password: (digite uma senha)
Retype new password: (repita a senha)
```

A partir daqui, sempre que este manual disser "abra o terminal do WSL", abra especificamente essa distro com `wsl -d Antigravity2`.

Depois disso, vá para a **Fase 1 (comum aos dois caminhos)**.

---

## Fase 1 — Instalar e configurar o SSH dentro do WSL

Dentro do terminal do **WSL** (a distro escolhida no Caminho A ou B):

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install openssh-server -y
```

Troque a porta padrão do SSH (22) para **2222**, para não colidir com nada que já use a porta 22 no Windows:

```bash
sudo sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
```

## Fase 2 — Habilitar systemd e deixar o SSH sempre ativo

Ainda no **WSL**, crie/edite o arquivo de configuração da distro:

```bash
sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[boot]
systemd=true
EOF
```

Feche o terminal do WSL. No **PowerShell**, reinicie a distro para aplicar a mudança:

```powershell
wsl --shutdown
wsl -d Antigravity2
```

(Se você seguiu o Caminho A com a distro padrão, use `wsl` em vez de `wsl -d Antigravity2`.)

De volta ao terminal do **WSL**, ative o serviço SSH para iniciar sozinho:

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh
```

O `status` deve mostrar `active (running)`. Com o systemd ativo e o SSH rodando como serviço, a distro tende a continuar em segundo plano — se um dia a conexão falhar, basta abrir o terminal dela de novo para "acordá-la".

## Fase 3 — Criar a chave SSH no Windows (autenticação sem senha)

No **PowerShell** (não precisa ser Admin):

```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\orca_antigravity" -N '""'
```

Isso cria duas chaves em `%USERPROFILE%\.ssh\`: `orca_antigravity` (privada) e `orca_antigravity.pub` (pública).

Mostre o conteúdo da chave pública:

```powershell
Get-Content "$env:USERPROFILE\.ssh\orca_antigravity.pub"
```

Copie a linha inteira (começa com `ssh-ed25519...`).

No terminal do **WSL**, cole essa chave em `authorized_keys`:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "COLE_AQUI_A_CHAVE_PUBLICA" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## Fase 4 — Testar a conexão SSH do Windows para o WSL

No **PowerShell**:

```powershell
ssh -p 2222 -i "$env:USERPROFILE\.ssh\orca_antigravity" seuusuario@localhost
```

(troque `seuusuario` pelo nome criado na Fase A.2 ou B.2). Se conectar sem pedir senha e cair no prompt do Ubuntu, funcionou. Digite `exit` para sair.

## Fase 5 — Instalar o Antigravity (agy) dentro do WSL e logar na segunda conta

No terminal do **WSL**:

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

Depois:

```bash
agy
```

Ele vai tentar abrir o navegador para login. Se não abrir sozinho (comum em WSL puro), instale o `wslu` para integrar com o navegador do Windows:

```bash
sudo apt install wslu -y
```

Rode `agy` de novo. Se mesmo assim não abrir automaticamente, ele imprime um link no terminal — copie e cole esse link no navegador do Windows manualmente, e faça login com a **segunda conta do Google**.

> Nota: se o login travar por causa do keyring (armazenamento seguro de credenciais), instale um keyring básico:
> ```bash
> sudo apt install gnome-keyring dbus-x11 -y
> ```
> e tente `agy` novamente.

## Fase 6 — Cadastrar esse host no Orca e criar o worktree

1. No Orca: **Settings → SSH → Add Target**
2. Preencha:
   - **Host**: `localhost` (ou `127.0.0.1`)
   - **Port**: `2222`
   - **User**: `seuusuario`
   - **Identity file**: `C:\Users\trcnologia\.ssh\orca_antigravity`
3. Clique em **Test** — deve conectar sem erro.
4. Clique em **Save**.
5. Ao criar um novo worktree, escolha esse SSH Target em vez de "Local".

Pronto: os agentes rodando nesse worktree vão usar o Antigravity logado com a segunda conta, dentro do WSL, enquanto o Windows continua usando a primeira conta normalmente.

## Repetindo para uma terceira conta (opcional)

Basta repetir o **Caminho B** com outro nome de distro (ex: `Antigravity3`), usando outra porta (ex: `2223`) na Fase 1, gerando outra chave SSH na Fase 3, e cadastrando um novo SSH Target no Orca.

## Referências

- Orca — SSH worktrees: https://www.onorca.dev/docs/ssh
- Orca — Remote worktrees recipe: https://www.onorca.dev/docs/recipes/remote-worktrees
- Antigravity CLI — instalação: https://antigravity.google/docs/cli/install/
- Antigravity CLI — uso: https://antigravity.google/docs/cli/using/
- PR do Orca lendo cota do Antigravity via SSH: https://github.com/stablyai/orca/pull/19209
