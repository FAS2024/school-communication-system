{% comment %} <script>
  $(document).ready(function () {
    const $form = $("#target-group-form");
    const $recipientsTableBody = $("#recipients-table tbody");
    const $selectAll = $("#select-all-recipients");
    const $communicationForm = $("#communication-form");

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

    function saveFilters() {
      const filters = {};
      $form.find("select, input[type=checkbox]").each(function () {
        const $el = $(this);
        filters[$el.attr("id")] = $el.is(":checkbox")
          ? $el.prop("checked")
          : $el.val();
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
          $el.is(":checkbox")
            ? $el.prop("checked", filters[id])
            : $el.val(filters[id]);
        }
      }
    }

    function updateBranchVisibility() {
      if (fields.branch.val()) {
        $("#role-field").show();
      } else {
        $(
          "#role-field, #staff-type-field, #teaching-positions-field, #non-teaching-positions-field, #student-class-field, #class-arm-field"
        ).hide();
        resetFields([
          "role",
          "staffType",
          "teaching",
          "nonTeaching",
          "studentClass",
          "classArm",
        ]);
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
        $(
          "#staff-type-field, #teaching-positions-field, #non-teaching-positions-field"
        ).hide();
        resetFields(["staffType", "teaching", "nonTeaching"]);
        $("#student-class-field").show();
        updateStudentClassVisibility();
      } else {
        $(
          "#staff-type-field, #teaching-positions-field, #non-teaching-positions-field, #student-class-field, #class-arm-field"
        ).hide();
        resetFields([
          "staffType",
          "teaching",
          "nonTeaching",
          "studentClass",
          "classArm",
        ]);
      }
    }

    function updateStaffTypeVisibility() {
      const type = fields.staffType.val();
      const $teachingField = $("#teaching-positions-field");
      const $nonTeachingField = $("#non-teaching-positions-field");

      switch (type) {
        case "teaching":
          $teachingField.show();
          $nonTeachingField.hide();
          fields.nonTeaching
            .find("input[type=checkbox]")
            .prop("checked", false);
          break;
        case "non_teaching":
          $teachingField.hide();
          $nonTeachingField.show();
          fields.teaching.find("input[type=checkbox]").prop("checked", false);
          break;
        case "both":
          $teachingField.show();
          $nonTeachingField.show();
          break;
        default:
          $teachingField.hide();
          $nonTeachingField.hide();
          fields.teaching.find("input[type=checkbox]").prop("checked", false);
          fields.nonTeaching
            .find("input[type=checkbox]")
            .prop("checked", false);
      }
    }

    function updateStudentClassVisibility() {
      const show = !!fields.studentClass.val();
      $("#class-arm-field").toggle(show);
      if (!show) fields.classArm.val("");
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

    function saveSelectedRecipients() {
      localStorage.setItem(
        "selectedRecipients",
        JSON.stringify([...selectedRecipients])
      );
    }

    function loadSelectedRecipients() {
      selectedRecipients = new Set(
        JSON.parse(localStorage.getItem("selectedRecipients") || "[]")
      );
    }

    function updateRecipientTableCheckboxStates() {
      $(".recipient-checkbox").each(function () {
        const id = $(this).val();
        $(this).prop("checked", selectedRecipients.has(id));
      });
      $selectAll.prop(
        "checked",
        $(".recipient-checkbox:checked").length ===
          $(".recipient-checkbox").length
      );
    }

    function loadRecipients() {
      $.get(
        "{% url 'get_filtered_users' %}",
        $form.serialize(),
        function (response) {
          $recipientsTableBody.empty();
          if (response.length === 0) {
            $recipientsTableBody.append(
              '<tr><td colspan="6" class="text-center p-4">No users found.</td></tr>'
            );
            $selectAll.prop("checked", false);
            return;
          }

          response.forEach((user, index) => {
            const profilePic =
              (user.profile_picture && user.profile_picture.url) ||
              "/static/assets/img/profile-pic.png";
            const isChecked = selectedRecipients.has(user.id.toString())
              ? "checked"
              : "";
            const row = `
            <tr style="border-bottom: 1px solid #eee;">
              <td class="text-center"><input type="checkbox" class="recipient-checkbox" value="${
                user.id
              }" ${isChecked}></td>
              <td class="text-center">${index + 1}</td>
              <td class="text-center"><img src="${profilePic}" alt="Profile Picture" width="30" height="30" style="border-radius: 50%; object-fit: cover;"></td>
              <td class="text-center">${user.branch__name}</td>
              <td>${user.first_name} ${user.last_name}</td>
              <td>${user.email}</td>
            </tr>`;
            $recipientsTableBody.append(row);
          });

          updateRecipientTableCheckboxStates();
        }
      );
    }

    function handleDependencyChange() {
      clearSelectedRecipients();
      $selectAll.prop("checked", false);
      saveFilters();
      loadRecipients();
    }

    // === Event Bindings ===
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

    $form
      .find("select, input[type=checkbox]")
      .not("#select-all-recipients")
      .on("change", handleDependencyChange);

    $recipientsTableBody.on("change", ".recipient-checkbox", function () {
      const id = $(this).val();
      $(this).is(":checked")
        ? selectedRecipients.add(id)
        : selectedRecipients.delete(id);
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

    $communicationForm.on("submit", function () {
      // Clear filters and recipients on submit
      clearFiltersStorage();
      clearSelectedRecipients();
      localStorage.removeItem("selectedRecipients");

      // Remove any old hidden inputs
      $communicationForm.find('input[name="selected_recipients"]').remove();

      [...selectedRecipients].forEach(function (id) {
        $("<input>", {
          type: "hidden",
          name: "selected_recipients",
          value: id,
        }).appendTo($communicationForm);
      });
    });

    // === Attachments ===

    const maxAttachments = 10;
    let totalForms = parseInt($("#id_attachments-TOTAL_FORMS").val());

    $("#add-attachment").on("click", function () {
      if (totalForms >= maxAttachments)
        return alert("Maximum attachments reached.");

      const $newForm = $(".attachment-form:first").clone();
      $newForm.find("input, select, textarea").each(function () {
        const name = $(this).attr("name").replace("-0-", `-${totalForms}-`);
        const id = "id_" + name;
        $(this).attr({ name, id }).val("");
        if ($(this).is(":checkbox, :radio")) $(this).prop("checked", false);
      });

      $newForm.find(".remove-attachment").remove();
      $newForm.append(
        '<button type="button" class="btn btn-danger remove-attachment" style="position: absolute; top: 10px; right: 10px;">Remove</button>'
      );
      $("#attachments-container").append($newForm);

      totalForms++;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });

    $("#attachments-container").on("click", ".remove-attachment", function () {
      $(this).closest(".attachment-form").remove();
      totalForms--;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });

    // === Initial Setup ===
    loadFilters();
    loadSelectedRecipients();
    updateBranchVisibility();
    updateRoleVisibility();
    updateStaffTypeVisibility();
    updateStudentClassVisibility();
    loadRecipients();
  });
</script>

<script>
  $(document).ready(function () {
    $('#recipients-table').DataTable();
  });
</script> {% endcomment %}



<script>
  $(document).ready(function () {
    const $form = $("#target-group-form");
    const $recipientsTableBody = $("#recipients-table tbody");
    const $selectAll = $("#select-all-recipients");
    const $communicationForm = $("#communication-form");

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

    function saveFilters() {
      const filters = {};
      $form.find("select, input[type=checkbox]").each(function () {
        const $el = $(this);
        filters[$el.attr("id")] = $el.is(":checkbox")
          ? $el.prop("checked")
          : $el.val();
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
          $el.is(":checkbox")
            ? $el.prop("checked", filters[id])
            : $el.val(filters[id]);
        }
      }
    }

    function updateBranchVisibility() {
      if (fields.branch.val()) {
        $("#role-field").show();
      } else {
        $(
          "#role-field, #staff-type-field, #teaching-positions-field, #non-teaching-positions-field, #student-class-field, #class-arm-field"
        ).hide();
        resetFields([
          "role",
          "staffType",
          "teaching",
          "nonTeaching",
          "studentClass",
          "classArm",
        ]);
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
        $(
          "#staff-type-field, #teaching-positions-field, #non-teaching-positions-field"
        ).hide();
        resetFields(["staffType", "teaching", "nonTeaching"]);
        $("#student-class-field").show();
        updateStudentClassVisibility();
      } else {
        $(
          "#staff-type-field, #teaching-positions-field, #non-teaching-positions-field, #student-class-field, #class-arm-field"
        ).hide();
        resetFields([
          "staffType",
          "teaching",
          "nonTeaching",
          "studentClass",
          "classArm",
        ]);
      }
    }

    function updateStaffTypeVisibility() {
      const type = fields.staffType.val();
      const $teachingField = $("#teaching-positions-field");
      const $nonTeachingField = $("#non-teaching-positions-field");

      switch (type) {
        case "teaching":
          $teachingField.show();
          $nonTeachingField.hide();
          fields.nonTeaching
            .find("input[type=checkbox]")
            .prop("checked", false);
          break;
        case "non_teaching":
          $teachingField.hide();
          $nonTeachingField.show();
          fields.teaching.find("input[type=checkbox]").prop("checked", false);
          break;
        case "both":
          $teachingField.show();
          $nonTeachingField.show();
          break;
        default:
          $teachingField.hide();
          $nonTeachingField.hide();
          fields.teaching.find("input[type=checkbox]").prop("checked", false);
          fields.nonTeaching
            .find("input[type=checkbox]")
            .prop("checked", false);
      }
    }

    function updateStudentClassVisibility() {
      const show = !!fields.studentClass.val();
      $("#class-arm-field").toggle(show);
      if (!show) fields.classArm.val("");
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

    function saveSelectedRecipients() {
      localStorage.setItem(
        "selectedRecipients",
        JSON.stringify([...selectedRecipients])
      );
    }

    function loadSelectedRecipients() {
      selectedRecipients = new Set(
        JSON.parse(localStorage.getItem("selectedRecipients") || "[]")
      );
    }

    function updateRecipientTableCheckboxStates() {
      $(".recipient-checkbox").each(function () {
        const id = $(this).val();
        $(this).prop("checked", selectedRecipients.has(id));
      });
      $selectAll.prop(
        "checked",
        $(".recipient-checkbox:checked").length ===
          $(".recipient-checkbox").length
      );
    }

    function loadRecipients() {
      $.get(
        "{% url 'get_filtered_users' %}",
        $form.serialize(),
        function (response) {
          $recipientsTableBody.empty();
          if (response.length === 0) {
            $recipientsTableBody.append(
              '<tr><td colspan="6" class="text-center p-4">No users found.</td></tr>'
            );
            $selectAll.prop("checked", false);
            return;
          }

          response.forEach((user, index) => {
            const profilePic =
              (user.profile_picture && user.profile_picture.url) ||
              "/static/assets/img/profile-pic.png";
            const isChecked = selectedRecipients.has(user.id.toString())
              ? "checked"
              : "";
            const row = `
            <tr style="border-bottom: 1px solid #eee;">
              <td class="text-center"><input type="checkbox" class="recipient-checkbox" value="${
                user.id
              }" ${isChecked}></td>
              <td class="text-center">${index + 1}</td>
              <td class="text-center"><img src="${profilePic}" alt="Profile Picture" width="30" height="30" style="border-radius: 50%; object-fit: cover;"></td>
              <td class="text-center">${user.branch__name}</td>
              <td>${user.first_name} ${user.last_name}</td>
              <td>${user.email}</td>
            </tr>`;
            $recipientsTableBody.append(row);
          });

          updateRecipientTableCheckboxStates();
        }
      );
    }

    function handleDependencyChange() {
      clearSelectedRecipients();
      $selectAll.prop("checked", false);
      saveFilters();
      loadRecipients();
    }

    // === Event Bindings ===
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

    $form
      .find("select, input[type=checkbox]")
      .not("#select-all-recipients")
      .on("change", handleDependencyChange);

    $recipientsTableBody.on("change", ".recipient-checkbox", function () {
      const id = $(this).val();
      $(this).is(":checked")
        ? selectedRecipients.add(id)
        : selectedRecipients.delete(id);
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

    $communicationForm.on("submit", function () {
      // Clear filters and recipients on submit
      clearFiltersStorage();
      clearSelectedRecipients();
      localStorage.removeItem("selectedRecipients");

      // Remove any old hidden inputs
      $communicationForm.find('input[name="selected_recipients"]').remove();

      [...selectedRecipients].forEach(function (id) {
        $("<input>", {
          type: "hidden",
          name: "selected_recipients",
          value: id,
        }).appendTo($communicationForm);
      });
    });

    // === Attachments ===

    const maxAttachments = 10;
    let totalForms = parseInt($("#id_attachments-TOTAL_FORMS").val());

    $("#add-attachment").on("click", function () {
      if (totalForms >= maxAttachments)
        return alert("Maximum attachments reached.");

      const $newForm = $(".attachment-form:first").clone();
      $newForm.find("input, select, textarea").each(function () {
        const name = $(this).attr("name").replace("-0-", `-${totalForms}-`);
        const id = "id_" + name;
        $(this).attr({ name, id }).val("");
        if ($(this).is(":checkbox, :radio")) $(this).prop("checked", false);
      });

      $newForm.find(".remove-attachment").remove();
      $newForm.append(
        '<button type="button" class="btn btn-danger remove-attachment" style="position: absolute; top: 10px; right: 10px;">Remove</button>'
      );
      $("#attachments-container").append($newForm);

      totalForms++;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });

    $("#attachments-container").on("click", ".remove-attachment", function () {
      $(this).closest(".attachment-form").remove();
      totalForms--;
      $("#id_attachments-TOTAL_FORMS").val(totalForms);
    });

    // === Initial Setup ===
    loadFilters();
    loadSelectedRecipients();
    updateBranchVisibility();
    updateRoleVisibility();
    updateStaffTypeVisibility();
    updateStudentClassVisibility();
    loadRecipients();
  });
</script>

<script>
  $(document).ready(function () {
    $("#recipients-table").DataTable({
      columnDefs: [
        {
          targets: 0, // First column (Select All / checkboxes)
          orderable: false,
          searchable: false,
        }
      ],
      order: [[1, 'asc']] // Optional: set default sorting by serial number
    });
  });
</script>
