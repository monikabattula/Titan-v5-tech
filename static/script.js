const dropArea = document.getElementById("drop-area");
const inputFile = document.getElementById("input-file");
const imgView = document.getElementById("img-view");
const upload = document.getElementById("upload");
const lang = document.getElementById("lang");
const lang2 = document.getElementById("lang-2");
const form = document.getElementById("form").reset();

inputFile.addEventListener("change", uploadImage);

function uploadImage() {
  const extensions = new Set([
    "mp4",
    "mov",
    "mkv",
    "avi",
    "wmv",
    "flv",
    "webm",
    "avchd",
  ]);
  const fileName = inputFile.files[0].name;
  let imgLink = URL.createObjectURL(inputFile.files[0]);
  const ext = fileName.split(".").pop();
  if (!extensions.has(ext.toLowerCase())) {
    alert("Invalid File Format");
    return;
  }
  imgView.innerHTML = `<video controls><source src=${imgLink}></video>`;
  imgView.style.border = 0;
}

dropArea.addEventListener("dragover", (e) => {
  e.preventDefault();
});

dropArea.addEventListener("drop", (e) => {
  e.preventDefault();
  inputFile.files = e.dataTransfer.files;
  uploadImage();
});

upload.addEventListener("click", (e) => {
  // if (!inputFile.files[0]) {
  //   alert("Please upload or select a video first");
  //   e.preventDefault();
  //   return;
  // }
  if (lang.value === "hide") {
    alert("Please select a language");
    e.preventDefault();
    return;
  }
  if (lang2.value === "hide") {
    alert("Please select a voice");
    e.preventDefault();
    return;
  } else {
    form.submit();
  }
});
