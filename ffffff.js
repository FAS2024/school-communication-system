<script>
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

    // ===== Utility Functions =====

    function areFiltersEmpty() {
      // Check if all filters are empty or unchecked
      for (const key in fields) {
        const field = fields[key];

        // Skip logic for fields not relevant to userRole
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
      // If no filters are applied, always show no users found message
      if (areFiltersEmpty()) {
        recipientsTable.clear().draw();
        $selectAll.prop("checked", false);
        $recipientsTableBody.html('<tr><td colspan="6" class="text-center p-4">No users found.</td></tr>');
        return;
      }

      // Extra safeguard for student role — avoid sending request if student_class or class_arm is empty
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

      const queryData = $form.serializeArray().filter(item => {
      const val = item.value && item.value.trim();
      if (!val) return false;

      const role = fields.role.val();
      const staffType = fields.staffType.val();

      // Skip irrelevant fields
      if (role !== "student" && (item.name === "student_class" || item.name === "class_arm")) return false;
      if (role !== "staff" && item.name === "staff_type") return false;

      // Require at least one teaching/non-teaching checkbox for staff_type 'both'
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

      // Only make request when queryData is not empty
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

    // ===== Event Bindings =====

    fields.branch.on("change", () => {
      updateBranchVisibility();
      updateRoleVisibility();
      handleDependencyChange();
    });

    fields.role.on("change", () => {
      updateRoleVisibility();
      handleDependencyChange();
    });

    fields.staffType.on("change", () => {
      updateStaffTypeVisibility();
      handleDependencyChange();
    });

    fields.studentClass.on("change", () => {
      updateStudentClassVisibility();
      handleDependencyChange();
    });

    $form.find("select, input[type=checkbox]").not("#select-all-recipients").on("change", handleDependencyChange);

    $recipientsTableBody.on("change", ".recipient-checkbox", function () {
      const id = $(this).val();
      if ($(this).is(":checked")) {
        selectedRecipients.add(id);
      } else {
        selectedRecipients.delete(id);
      }
      saveSelectedRecipients();
      updateRecipientTableCheckboxStates();
    });

    $selectAll.on("change", function () {
      const checked = this.checked;
      $(".recipient-checkbox").each(function () {
        $(this).prop("checked", checked);
        const id = $(this).val();
        if (checked) {
          selectedRecipients.add(id);
        } else {
          selectedRecipients.delete(id);
        }
      });
      saveSelectedRecipients();
    });

    $communicationForm.on("submit", function (e) {
      if (["staff", "branch_admin", "superadmin"].includes(userRole) && !fields.branch.val()) {
        alert("Please select a Branch before submitting the form.");
        e.preventDefault();
        return false;
      }

      if (["student", "parent"].includes(userRole) && !fields.role.val()) {
        alert("Please select a Role before submitting the form.");
        e.preventDefault();
        return false;
      }

      clearFiltersStorage();
      clearSelectedRecipients();

      $communicationForm.find('input[name="selected_recipients"]').remove();

      [...selectedRecipients].forEach(function (id) {
        $("<input>", {
          type: "hidden",
          name: "selected_recipients",
          value: id,
        }).appendTo($communicationForm);
      });
    });

    // ===== Attachments =====

    const maxAttachments = 10;
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
      $newForm.append('<button type="button" class="btn btn-danger remove-attachment" style="position: absolute; top: 10px; right: 10px;">Remove</button>');
      $("#attachments-container").append($newForm);

      totalForms++;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });

    $("#attachments-container").on("click", ".remove-attachment", function () {
      $(this).closest(".attachment-form").remove();
      totalForms--;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });


    // ===== Initial Load =====

    loadFilters();
    loadSelectedRecipients();
    updateBranchVisibility();
    updateRoleVisibility();
    updateStaffTypeVisibility();
    updateStudentClassVisibility();
    loadRecipients();
  });
</script> 
