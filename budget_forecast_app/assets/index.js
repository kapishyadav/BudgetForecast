function component() {
  const element = document.createElement('div');
  element.innerHTML = 'Hello Vite with HMR! COOL!';
  return element;
}
document.body.appendChild(component());