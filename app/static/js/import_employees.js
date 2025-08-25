document.addEventListener('DOMContentLoaded', () => {
  const dropZone = document.getElementById('importDropZone');
  const fileInput = document.getElementById('importEmployeesFile');
  const uploadBtn = document.getElementById('importUploadBtn');
  const form = document.getElementById('importForm');
  const fileNameLabel = document.getElementById('selectedFileName');

  if (!dropZone || !fileInput || !uploadBtn || !form) return;

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('bg-light');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('bg-light');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('bg-light');
    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      handleFileChosen();
    }
  });

  fileInput.addEventListener('change', handleFileChosen);

  function handleFileChosen() {
    if (fileInput.files.length) {
      const name = fileInput.files[0].name;
      if (fileNameLabel) {
        fileNameLabel.textContent = name;
        fileNameLabel.classList.remove('d-none');
      }
      dropZone.classList.add('border-success');
      uploadBtn.disabled = false;
    } else {
      if (fileNameLabel) {
        fileNameLabel.textContent = '';
        fileNameLabel.classList.add('d-none');
      }
      dropZone.classList.remove('border-success');
      uploadBtn.disabled = true;
    }
  }

  uploadBtn.addEventListener('click', () => {
    if (!fileInput.files.length) {
      alert('Please choose a file to upload.');
      return;
    }
    form.submit();
  });
});
