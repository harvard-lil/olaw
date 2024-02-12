/*------------------------------------------------------------------------------
 * Open targeted dialog using data-dialog
 -----------------------------------------------------------------------------*/
for (const dialogOpenButton of document.querySelectorAll("button[data-dialog]")) {
  
  dialogOpenButton.addEventListener("click", e => {
    e.preventDefault();

    for (const dialog of document.querySelectorAll("dialog")) {
      if (dialog.classList.contains(dialogOpenButton.dataset.dialog)) {
        dialog.showModal();
        continue;
      } 

      // Close non-target dialogs in case they're open
      if (dialog.open === true) {
        dialog.close();
      }
    }
  });
}

for (const dialogCloseButton of document.querySelectorAll("dialog button.close")) {
  dialogCloseButton.addEventListener("click", e => {
    e.preventDefault();
    e.target.parentNode.close();
  })
}