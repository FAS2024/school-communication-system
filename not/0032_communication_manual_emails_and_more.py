<!-- jQuery -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<!-- SweetAlert2 CDN -->
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>

<script>
  let recipientsTable;

  $(document).ready(function () {
    const $form = $("#target-group-form");
    const $recipientsTableBody = $("#recipients-table tbody");
    const $selectAll = $("#select-all-recipients");
    const $communicationForm = $("#communication-form");
    const userRole = $communicationForm.data("user-role");

    const fields = {
      branch: $("#id_branch"),
      role: $("#id_role"),
      staffType: $("#id_staff_type"),
      teaching: $("#id_teaching_positions"),
      nonTeaching: $("#id_non_teaching_positions"),
      studentClass: $("#id_student_class"),
      classArm: $("#id_class_arm"),
    };

    let selectedRecipients = new Set();

    // ===== Initialize DataTable =====
    if (!$.fn.DataTable.isDataTable("#recipients-table")) {
      recipientsTable = $("#recipients-table").DataTable({
        columnDefs: [{ targets: 0, orderable: false, searchable: false }],
        order: [[1, "asc"]],
      });
    } else {
      recipientsTable = $("#recipients-table").DataTable();
    }

    // ===== Utility Functions =====
    function areFiltersEmpty() {
      for (const key in fields) {
        const field = fields[key];
        if ((userRole === "student" || userRole === "parent") && key !== "role") continue;
        if ((userRole !== "student" && userRole !== "parent") && key === "role") continue;
        if (field.is(":checkbox")) {
          if (field.prop("checked")) return false;
        } else {
          const val = field.val();
          if (val && val.toString().trim() !== "" && val !== "------------") return false;
        }
      }
      return true;
    }

    function saveFilters() {
      const filters = {};
      $form.find("select, input[type=checkbox]").each(function () {
        const $el = $(this);
        filters[$el.attr("id")] = $el.is(":checkbox") ? $el.prop("checked") : $el.val();
      });
      localStorage.setItem("targetGroupFilters", JSON.stringify(filters));
    }

    function clearFiltersStorage() {
      localStorage.removeItem("targetGroupFilters");
    }

    function clearSelectedRecipients() {
      selectedRecipients.clear();
      localStorage.removeItem("selectedRecipients");
    }

    function loadFilters() {
      const saved = localStorage.getItem("targetGroupFilters");
      if (!saved) return;
      const filters = JSON.parse(saved);
      for (const id in filters) {
        const $el = $("#" + id);
        if ($el.length) {
          if ($el.is(":checkbox")) {
            $el.prop("checked", filters[id]);
          } else {
            $el.val(filters[id]);
          }
        }
      }
    }

    function resetFields(keys) {
      keys.forEach((key) => {
        const field = fields[key];
        if (field.is("select")) {
          field.val("");
        } else {
          field.find("input[type=checkbox]").prop("checked", false);
        }
      });
    }

    function updateBranchVisibility() {
      if (fields.branch.val()) {
        $("#role-field").show();
      } else {
        $("#role-field, #staff-type-field, #teaching-positions-field, #non-teaching-positions-field, #student-class-field, #class-arm-field").hide();
        resetFields(["role", "staffType", "teaching", "nonTeaching", "studentClass", "classArm"]);
      }
    }

    function updateRoleVisibility() {
      const role = fields.role.val();
      if (role === "staff") {
        $("#staff-type-field").show();
        $("#student-class-field, #class-arm-field").hide();
        resetFields(["studentClass", "classArm"]);
        updateStaffTypeVisibility();
      } else if (role === "student") {
        $("#staff-type-field, #teaching-positions-field, #non-teaching-positions-field").hide();
        resetFields(["staffType", "teaching", "nonTeaching"]);
        $("#student-class-field").show();
        updateStudentClassVisibility();
      } else {
        $("#staff-type-field, #teaching-positions-field, #non-teaching-positions-field, #student-class-field, #class-arm-field").hide();
        resetFields(["staffType", "teaching", "nonTeaching", "studentClass", "classArm"]);
      }
    }

    function updateStaffTypeVisibility() {
      const type = fields.staffType.val();
      const $teaching = $("#teaching-positions-field");
      const $nonTeaching = $("#non-teaching-positions-field");

      if (type === "teaching") {
        $teaching.show();
        $nonTeaching.hide().find("input[type=checkbox]").prop("checked", false);
      } else if (type === "non_teaching") {
        $nonTeaching.show();
        $teaching.hide().find("input[type=checkbox]").prop("checked", false);
      } else if (type === "both") {
        $teaching.show();
        $nonTeaching.show();
      } else {
        $teaching.hide().find("input[type=checkbox]").prop("checked", false);
        $nonTeaching.hide().find("input[type=checkbox]").prop("checked", false);
      }
    }

    function updateStudentClassVisibility() {
      const show = !!fields.studentClass.val();
      $("#class-arm-field").toggle(show);
      if (!show) fields.classArm.val("");
    }

    function saveSelectedRecipients() {
      localStorage.setItem("selectedRecipients", JSON.stringify([...selectedRecipients]));
    }

    function loadSelectedRecipients() {
      selectedRecipients = new Set(JSON.parse(localStorage.getItem("selectedRecipients") || "[]"));
    }

    function updateRecipientTableCheckboxStates() {
      $(".recipient-checkbox").each(function () {
        const id = $(this).val();
        $(this).prop("checked", selectedRecipients.has(id));
      });
      $selectAll.prop(
        "checked",
        $(".recipient-checkbox:checked").length === $(".recipient-checkbox").length
      );
    }

    function loadRecipients() {
      if (areFiltersEmpty()) {
        recipientsTable.clear().draw();
        $selectAll.prop("checked", false);
        $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">No users found.</td></tr>');
        return;
      }

      if (userRole === "student") {
        if (fields.role.val() === "student") {
          const studentClass = fields.studentClass.val();
          const classArm = fields.classArm.val();
          if (!studentClass || !classArm) {
            recipientsTable.clear().draw();
            $selectAll.prop("checked", false);
            $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select class and arm to view students.</td></tr>');
            return;
          }
        }
      }

      const queryData = $form.serializeArray().filter(item => {
        const val = item.value && item.value.trim();
        if (!val) return false;

        const role = fields.role.val();
        const staffType = fields.staffType.val();

        if (role !== "student" && (item.name === "student_class" || item.name === "class_arm")) return false;
        if (role !== "staff" && item.name === "staff_type") return false;

        if (role === "staff") {
          const hasTeaching = fields.teaching.find("input:checked").length > 0;
          const hasNonTeaching = fields.nonTeaching.find("input:checked").length > 0;

          if (staffType === "both" && !hasTeaching && !hasNonTeaching) {
            recipientsTable.clear().draw();
            $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select at least one Teaching or Non-Teaching position.</td></tr>');
            return false;
          }

          if (staffType === "non_teaching" && !hasNonTeaching) {
            recipientsTable.clear().draw();
            $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select at least one Non-Teaching position.</td></tr>');
            return false;
          }

          if (staffType === "teaching" && !hasTeaching) {
            recipientsTable.clear().draw();
            $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please select at least one Teaching position.</td></tr>');
            return false;
          }
        }

        return true;
      });

      if (queryData.length === 0) {
        recipientsTable.clear().draw();
        $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">Please apply valid filters to see results.</td></tr>');
        return;
      }

      $.get("{% url 'get_filtered_users' %}", $.param(queryData), function (response) {
        recipientsTable.clear();
        if (response.length === 0) {
          recipientsTable.draw();
          $selectAll.prop("checked", false);
          $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">No users found.</td></tr>');
          return;
        }

        response.forEach((user, index) => {
          const profilePic = (user.profile_picture && user.profile_picture.url) || "/static/assets/img/profile-pic.png";
          const isChecked = selectedRecipients.has(user.id.toString());

          recipientsTable.row.add([
            `<input type="checkbox" class="recipient-checkbox" value="${user.id}" ${isChecked ? "checked" : ""}>`,
            index + 1,
            `<img src="${profilePic}" alt="Profile Picture" width="30" height="30" style="border-radius: 50%; object-fit: cover;">`,
            user.branch__name,
            `${user.first_name} ${user.last_name}`,
            user.email,
          ]);
        });

        recipientsTable.draw();
        updateRecipientTableCheckboxStates();
      });
    }

    function handleDependencyChange() {
      clearSelectedRecipients();
      $selectAll.prop("checked", false);
      saveFilters();
      loadRecipients();
    }

    // ===== Events =====
    fields.branch.on("change", () => {
      updateBranchVisibility(); updateRoleVisibility(); handleDependencyChange();
    });

    fields.role.on("change", () => {
      updateRoleVisibility(); handleDependencyChange();
    });

    fields.staffType.on("change", () => {
      updateStaffTypeVisibility(); handleDependencyChange();
    });

    fields.studentClass.on("change", () => {
      updateStudentClassVisibility(); handleDependencyChange();
    });

    $form.find("select, input[type=checkbox]").not("#select-all-recipients").on("change", handleDependencyChange);

    $recipientsTableBody.on("change", ".recipient-checkbox", function () {
      const id = $(this).val();
      $(this).is(":checked") ? selectedRecipients.add(id) : selectedRecipients.delete(id);
      saveSelectedRecipients();
      updateRecipientTableCheckboxStates();
    });

    $selectAll.on("change", function () {
      const checked = this.checked;
      $(".recipient-checkbox").each(function () {
        $(this).prop("checked", checked);
        const id = $(this).val();
        checked ? selectedRecipients.add(id) : selectedRecipients.delete(id);
      });
      saveSelectedRecipients();
    });

    // Save as Draft validation with SweetAlert
    $("#save-draft").on("click", function (e) {
      const isDraftChecked = $("#id_is_draft").is(":checked");
      if (!isDraftChecked) {
        e.preventDefault();
        Swal.fire({
          title: "Draft Not Checked",
          text: "Please check 'Save as Draft' before saving.",
          icon: "warning",
          confirmButtonColor: "#3085d6",
          confirmButtonText: "OK"
        });
        return false;
      }

      saveFilters();
      saveSelectedRecipients();
    });

    // Submit validation with SweetAlert
    $communicationForm.on("submit", function (e) {
      const isDraftChecked = $("#id_is_draft").is(":checked");
      const submitButton = document.activeElement;

      if ($(submitButton).val() === "send" && isDraftChecked) {
        e.preventDefault();
        Swal.fire({
          title: "Draft is Checked",
          text: "You cannot send a message while 'Save as Draft' is checked. Please uncheck it to proceed.",
          icon: "error",
          confirmButtonColor: "#3085d6",
          confirmButtonText: "OK"
        });
        return false;
      }

      // Branch and role validation
      if (["staff", "branch_admin", "superadmin"].includes(userRole) && !fields.branch.val()) {
        e.preventDefault();
        Swal.fire({
          title: "Missing Branch",
          text: "Please select a Branch before submitting the form.",
          icon: "warning",
          confirmButtonColor: "#3085d6",
          confirmButtonText: "OK"
        });
        return false;
      }

      if (["student", "parent"].includes(userRole) && !fields.role.val()) {
        e.preventDefault();
        Swal.fire({
          title: "Missing Role",
          text: "Please select a Role before submitting the form.",
          icon: "warning",
          confirmButtonColor: "#3085d6",
          confirmButtonText: "OK"
        });
        return false;
      }

      // Proceed with submission
      $communicationForm.find(".injected-filter-field").remove();
      const filterFieldNames = ["branch", "role", "staff_type", "teaching_positions", "non_teaching_positions", "student_class", "class_arm"];

      filterFieldNames.forEach(function (name) {
        const $fields = $("#target-group-form [name='" + name + "']");
        if ($fields.length && $fields[0].type === "checkbox") {
          $fields.filter(":checked").each(function () {
            $("<input>", {
              type: "hidden",
              name,
              value: $(this).val(),
              class: "injected-filter-field"
            }).appendTo($communicationForm);
          });
        } else {
          const val = $fields.val();
          if (Array.isArray(val)) {
            val.forEach(function (item) {
              $("<input>", {
                type: "hidden",
                name,
                value: item,
                class: "injected-filter-field"
              }).appendTo($communicationForm);
            });
          } else if (val !== undefined && val !== null && val !== "") {
            $("<input>", {
              type: "hidden",
              name,
              value: val,
              class: "injected-filter-field"
            }).appendTo($communicationForm);
          }
        }
      });

      $communicationForm.find('input[name="selected_recipients"]').remove();
      [...selectedRecipients].forEach(function (id) {
        $("<input>", {
          type: "hidden",
          name: "selected_recipients",
          value: id
        }).appendTo($communicationForm);
      });

      const isFinalSend = $("#id_status").val() === "sent";
      if (isFinalSend && typeof clearFiltersStorage === "function") {
        clearFiltersStorage();
        localStorage.removeItem("selectedRecipients");
      }

      $communicationForm.off("submit").submit();
    });


    // ===== Attachment Handling =====
    const maxAttachments = 5;
    let totalForms = parseInt($("#id_attachments-TOTAL_FORMS").val());

    $("#add-attachment").on("click", function () {
      if (totalForms >= maxAttachments) return alert("Maximum attachments reached.");
      const $newForm = $(".attachment-form:first").clone();
      $newForm.find("input, select, textarea").each(function () {
        const name = $(this).attr("name").replace("-0-", `-${totalForms}-`);
        const id = "id_" + name;
        $(this).attr({ name, id }).val("");
        if ($(this).is(":checkbox, :radio")) $(this).prop("checked", false);
      });
      $newForm.find(".remove-attachment").remove();
      $newForm.append(`
        <button type="button" class="btn btn-sm btn-danger remove-attachment" 
                style="position: absolute; top: 8px; right: 8px; font-size: 0.75rem; padding: 2px 6px;">
          <i class="fas fa-times"></i>
        </button>
      `);
      $("#attachments-container").append($newForm);
      totalForms++;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });

    $("#attachments-container").on("click", ".remove-attachment", function () {
      $(this).closest(".attachment-form").remove();
      totalForms--;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });

    // ====== For saving Filters =======
    function syncFilterDataToHiddenFields() {
      document.getElementById('hidden-branch').value = document.getElementById('id_branch')?.value || '';
      document.getElementById('hidden-role').value = document.getElementById('id_role')?.value || '';
      document.getElementById('hidden-staff-type').value = document.getElementById('id_staff_type')?.value || '';
      document.getElementById('hidden-student-class').value = document.getElementById('id_student_class')?.value || '';
      document.getElementById('hidden-class-arm').value = document.getElementById('id_class_arm')?.value || '';

      // For multi-selects (teaching/non-teaching positions)
      const teachingPositions = Array.from(document.getElementById('id_teaching_positions')?.selectedOptions || []).map(opt => opt.value);
      const nonTeachingPositions = Array.from(document.getElementById('id_non_teaching_positions')?.selectedOptions || []).map(opt => opt.value);

      document.getElementById('hidden-teaching-positions').value = teachingPositions.join(',');
      document.getElementById('hidden-non-teaching-positions').value = nonTeachingPositions.join(',');
    }

    // ===== Initial Setup =====
    loadFilters();
    loadSelectedRecipients();
    updateBranchVisibility();
    updateRoleVisibility();
    updateStaffTypeVisibility();
    updateStudentClassVisibility();
    loadRecipients();
    syncFilterDataToHiddenFields();
  });
</script>
