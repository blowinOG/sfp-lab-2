const TOKEN_KEY = "vault_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

async function api(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

async function gql(query, variables = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch("/graphql", {
    method: "POST",
    headers,
    body: JSON.stringify({ query, variables }),
  });
  const json = await res.json();
  if (json.errors && json.errors.length) {
    throw new Error(json.errors.map(e => e.message).join("; "));
  }
  return json.data;
}

function show(el, visible) {
  el.classList.toggle("hidden", !visible);
}

const loginBlock = document.getElementById("login-block");
const adminBlock = document.getElementById("admin-block");
const errorBox = document.getElementById("error");
const clientsTbody = document.querySelector("#clients-table tbody");

function renderClients(clients) {
  clientsTbody.innerHTML = "";
  for (const c of clients) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${c.id}</td>
      <td>${c.clientId}</td>
      <td>${c.name}</td>
      <td>${c.isConfidential}</td>
      <td>${c.createdAt}</td>`;
    clientsTbody.appendChild(tr);
  }
}

async function loadClients() {
  const data = await gql(`{ clients { id clientId name isConfidential createdAt } }`);
  renderClients(data.clients);
}

document.getElementById("login-btn").addEventListener("click", async () => {
  errorBox.textContent = "";
  try {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const data = await api("/auth/login", { email, password });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    show(loginBlock, false);
    show(adminBlock, true);
    await loadClients();
  } catch (e) {
    errorBox.textContent = e.message;
  }
});

document.getElementById("logout-btn").addEventListener("click", () => {
  localStorage.removeItem(TOKEN_KEY);
  show(adminBlock, false);
  show(loginBlock, true);
  clientsTbody.innerHTML = "";
});

document.getElementById("create-client-btn").addEventListener("click", async () => {
  errorBox.textContent = "";
  try {
    const name = document.getElementById("client-name").value.trim() || "New client";
    await gql(
      `mutation($name: String!) { createClient(name: $name) { id clientId name isConfidential createdAt } }`,
      { name }
    );
    document.getElementById("client-name").value = "";
    await loadClients();
  } catch (e) {
    errorBox.textContent = e.message;
  }
});

if (getToken()) {
  show(loginBlock, false);
  show(adminBlock, true);
  loadClients().catch(err => {
    console.error(err);
    localStorage.removeItem(TOKEN_KEY);
    show(adminBlock, false);
    show(loginBlock, true);
  });
}