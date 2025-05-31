<template>
  <div class="q-pa-md">
    <q-layout view="hHh lpR fFf">
      <q-page-container>
        <q-page class="q-pa-md">
          <div class="q-pa-md">
            <q-card-section>
              <div class="row q-col-gutter-md">
                
                <!-- Left Section: File Upload & Process Data -->
                <div class="col-md-3 col-xs-12">
                  <q-file 
  v-model="files" 
  label="Upload EJ Log Files" 
  filled 
  multiple 
  class="q-mb-md" 
/>

<!-- Display selected files in a column -->
<q-card v-if="files.length" class="q-mt-md">
  <q-card-section>
    <div class="text-subtitle1">Selected Files:</div>
    <q-list separator bordered class="q-mt-sm">
      <q-item v-for="(file, index) in files" :key="index">
        <q-item-section>
          <q-item-label>{{ file.name }}</q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-btn flat round dense icon="delete" @click="removeFile(index)" color="red" />
        </q-item-section>
      </q-item>
    </q-list>
  </q-card-section>
</q-card>


                  <q-btn
                    color="primary"
                    label="Process Data"
                    class="q-mt-md full-width"
                    icon="play_arrow"
                    no-caps
                    :disable="files.length === 0"
                    @click="uploadAndProcessFiles"
                  />
                </div>

                <!-- Right Section: Filters & Table -->
                <div class="col-md-9 col-xs-12">
                  <div class="row q-mb-md q-gutter-md">
                    
                    <!-- Date & Time Filters -->
                     <!-- Date & Time Filters (Combined Date-Time) -->
                    <q-input v-model="fromDate" label="From Date" type="date" dense filled class="col-md-3 col-xs-12" />
                    <q-input v-model="fromTime" label="From Time" type="time" dense filled class="col-md-3 col-xs-12" />
                    <q-input v-model="toDate" label="To Date" type="date" dense filled class="col-md-3 col-xs-12" />
                    <q-input v-model="toTime" label="To Time" type="time" dense filled class="col-md-3 col-xs-12" />

                    <!-- Filter Category Dropdown -->
                    <q-select 
                    v-model="selectedFilterCategory" 
                    :options="filterCategories"
                    label="Filter By" 
                    dense 
                    filled 
                    class="col-md-3 col-xs-12"
                    emit-value
                    map-options
                    clearable
                    menu-anchor="bottom left"  
                    menu-self="top left"    
                    behavior="menu"          
                  />


                    <!-- Dynamic Value Dropdown/Input -->
                    <q-select 
                      v-if="isDropdownFilter"
                      v-model="selectedFilterValue"
                      :options="dynamicFilterOptions"
                      label="Select Value"
                      dense 
                      filled
                      class="col-md-3 col-xs-12"
                      emit-value
                      map-options
                      clearable
                      use-input  
                      input-debounce="300" 
                      @filter="filterDropdownOptions"  
                    />


                    <q-input 
                      v-else
                      v-model="selectedFilterValue"
                      label="Enter Value"
                      dense filled
                      class="col-md-3 col-xs-12"
                    />

                    <!-- Reset Button -->
                    <q-btn 
                      color="blue" 
                      icon="refresh"  
                      class="q-ml-md" 
                      @click="resetFilters"
                    />
                  </div>

                  <!-- Loading Indicator -->
                  <q-inner-loading :showing="loading">
                    <q-spinner-gears size="50px" color="primary" />
                  </q-inner-loading>

                  <!-- Search Input & Export -->
                  <div class="row items-center q-mb-md">
                    <q-input
                      dense
                      debounce="300"
                      v-model="search"
                      placeholder="Search..."
                      class="q-mr-md"
                    />
                    <q-btn color="primary" icon-right="archive" label="Export to CSV" no-caps @click="exportTable" />
                  </div>

                  <!-- Transaction Table -->
                  <q-table
                    flat
                    bordered
                    title="Extracted Transaction Data"
                    :rows="filteredRows"
                    :columns="columns"
                    row-key="transaction_id"
                    
                  >
                  </q-table>


                </div>
              </div>
            </q-card-section>
          </div>
        </q-page>
        <!--popup-->
        <q-dialog v-model="isDialogOpen">
          <q-card style="width: 600px; max-width: 90vw;">
            <q-card-section>
              <div class="text-h6">EJ Log Data</div>
            </q-card-section>

            <q-separator />

            <q-card-section style="max-height: 400px; overflow-y: auto;">
              <pre>{{ selectedTransactionLog }}</pre>
            </q-card-section>

            <q-separator />

            <q-card-actions align="right">
              <q-btn flat label="Close" color="primary" v-close-popup />
            </q-card-actions>
          </q-card>
        </q-dialog>


      </q-page-container>
    </q-layout>
  </div>
</template>

<script>
import { ref, computed } from "vue";
import { useQuasar } from "quasar";
import axios from "axios";
import { exportFile } from "quasar";
//import { date } from "quasar";
// const isDialogOpen = ref(false);
// const selectedTransactionLog = ref("");

export default {
  setup() {
    const $q = useQuasar();
    const files = ref([]);
    const search = ref("");
    const fromDate = ref("");
    const toDate = ref("");
    const fromTime = ref("");
    const toTime = ref("");
    const rows = ref([]); // ✅ Store extracted transactions
    const loading = ref(false);
    const selectedFilterCategory = ref(null); // ✅ Selected filter type (STAN, Card Number, etc.)
    const selectedFilterValue = ref(null); // ✅ Selected value for filtering

   
// ✅ Function to remove a file from the list
const removeFile = (index) => {
  files.value.splice(index, 1);
};

    // ✅ Table Columns
    const columns = ref([
      //{ name: "transaction_id", label: "Transaction ID", field: "transaction_id", sortable: true },
      { name: "timestamp", label: "Timestamp", field: "timestamp", sortable: true },
      { name: "card_number", label: "Card Number", field: "card_number", sortable: true },
      { name: "transaction_type", label: "Transaction Type", field: "transaction_type", sortable: true },
      { name: "amount", label: "Amount", field: "amount", sortable: true },
      { name: "response_code", label: "Response Code", field: "response_code", sortable: true },
      { name: "account_number", label: "Account Number", field: "account_number", sortable: true },
      { name: "terminal", label: "Terminal", field: "terminal", sortable: true },
      { name: "transaction_number", label: "Transaction Number", field: "transaction_number", sortable: true },
      { name: "stan", label: "STAN", field: "stan", sortable: true },
      { name: "file_name", label: "File Name", field: "file_name", sortable: true },

      // ✅ Dispensed Notes
      { name: "dispensed_type1", label: "Dispensed Type 1", field: "dispensed_type1", sortable: true },
      { name: "dispensed_type2", label: "Dispensed Type 2", field: "dispensed_type2", sortable: true },
      { name: "dispensed_type3", label: "Dispensed Type 3", field: "dispensed_type3", sortable: true },
      { name: "dispensed_type4", label: "Dispensed Type 4", field: "dispensed_type4", sortable: true },
      { name: "total_dispensed", label: "Total Dispensed", field: "total_dispensed", sortable: true },

      // ✅ Rejected Notes
      { name: "rejected_type1", label: "Rejected Type 1", field: "rejected_type1", sortable: true },
      { name: "rejected_type2", label: "Rejected Type 2", field: "rejected_type2", sortable: true },
      { name: "rejected_type3", label: "Rejected Type 3", field: "rejected_type3", sortable: true },
      { name: "rejected_type4", label: "Rejected Type 4", field: "rejected_type4", sortable: true },

      // ✅ Remaining Notes in ATM
      { name: "remaining_type1", label: "Remaining Type 1", field: "remaining_type1", sortable: true },
      { name: "remaining_type2", label: "Remaining Type 2", field: "remaining_type2", sortable: true },
      { name: "remaining_type3", label: "Remaining Type 3", field: "remaining_type3", sortable: true },
      { name: "remaining_type4", label: "Remaining Type 4", field: "remaining_type4", sortable: true }
    ]);

    // ✅ Available Filter Categories
    const filterCategories = ref([
  { label: "STAN", value: "stan" },
  { label: "Card Number", value: "card_number" },
  { label: "Amount", value: "amount" },
  { label: "Response Code", value: "response_code" },
  { label: "Terminal", value: "terminal" }
]);

// const selectedFilterCategory = ref(null);
// const selectedFilterValue = ref(null);
const allFilterOptions = ref([]);  // ✅ Stores all options for the selected filter
const dynamicFilterOptions = ref([]);  // ✅ Stores filtered dropdown options

// ✅ Function to update filter values when filter category changes
function updateFilterValues() {
  selectedFilterValue.value = null;
  if (!selectedFilterCategory.value) {
    allFilterOptions.value = [];
    dynamicFilterOptions.value = [];
    return;
  }

  const field = selectedFilterCategory.value;
  const uniqueValues = new Set(rows.value.map(row => row[field]).filter(val => val));
  allFilterOptions.value = Array.from(uniqueValues).map(val => ({ label: val, value: val })).sort((a, b) => a.label.localeCompare(b.label));
  dynamicFilterOptions.value = [...allFilterOptions.value];  // ✅ Initially, show all options
}

// ✅ Function to filter dropdown options based on input
function filterDropdownOptions(val, update) {
  if (!val) {
    update(() => {
      dynamicFilterOptions.value = [...allFilterOptions.value];  // ✅ Reset to all options when empty
    });
    return;
  }

  update(() => {
    dynamicFilterOptions.value = allFilterOptions.value.filter(option =>
      option.label.toLowerCase().includes(val.toLowerCase())
    );
  });
}

// ✅ Check if the filter category should use a dropdown
const isDropdownFilter = computed(() => selectedFilterCategory.value && allFilterOptions.value.length > 0);


    // ✅ Upload and Process Files
    async function uploadAndProcessFiles() {
      if (files.value.length === 0) {
        alert("Please select at least one file.");
        return;
      }

      let formData = new FormData();
      files.value.forEach((file) => formData.append("files", file));

      loading.value = true;

      try {
        const response = await axios.post("http://localhost:5000/api/ej/load_logs", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        console.log("✅ API Response:", response.data);

        if (response.data.transactions) {
          rows.value = response.data.transactions;
        } else {
          rows.value = [];
        }
      } catch (error) {
        console.error("❌ API call failed:", error);
        alert("Failed to process file.");
      } finally {
        loading.value = false;
      }
    }
    
    
    // ✅ Filter Rows Based on Selection
    // const filteredRows1 = computed(() => {
    //   return rows.value.filter(row => {
    //     const matchesCategory = selectedFilterCategory.value
    //       ? row[selectedFilterCategory.value] == selectedFilterValue.value
    //       : true;

    //     return matchesCategory;
    //   });
    // });

//     const filteredRows = computed(() => {
//   return rows.value.filter(row => {
//     if (!row.timestamp) return false; // Ensure row has a timestamp

//     const [rowDateStr, rowTimeStr] = row.timestamp.split(" "); // ✅ Extract Date & Time
//     if (!rowDateStr || !rowTimeStr) return false; // ✅ Ignore invalid data


//     const rowDate = new Date(
//       `20${rowDateStr.split("/")[2]}-${rowDateStr.split("/")[1]}-${rowDateStr.split("/")[0]}`
//     ); // ✅ Convert "DD/MM/YY" → "YYYY-MM-DD"

//     const rowTime = rowTimeStr; // ✅ Time remains unchanged

//     // ✅ Date Filters (if selected)
//     const fromDateValid = fromDate.value ? new Date(fromDate.value) <= rowDate : true;
//     const toDateValid = toDate.value ? new Date(toDate.value) >= rowDate : true;

//     // ✅ Time Filters (if selected)
//     const fromTimeValid = fromTime.value ? fromTime.value <= rowTime : true;
//     const toTimeValid = toTime.value ? toTime.value >= rowTime : true;

//     // ✅ Apply Category Filtering
//     const matchesCategory = selectedFilterCategory.value
//       ? row[selectedFilterCategory.value]?.toString().includes(selectedFilterValue.value || "")
//       : true;

//     // ✅ Apply Search Input Filtering (case insensitive)
//     const matchesSearch = search.value
//       ? Object.values(row).some(value =>
//           value?.toString().toLowerCase().includes(search.value.toLowerCase())
//         )
//       : true;

//     return fromDateValid && toDateValid && fromTimeValid && toTimeValid &&  matchesCategory && matchesSearch;
//   });
// });
 // ✅ Function to Convert "DD/MM/YY HH:MM:SS" → JavaScript Date
 function parseDateTime(dateStr) {
  if (!dateStr) return null;

  // ✅ Ensure timestamp is in "DD/MM/YY HH:MM:SS" format
  const [datePart, timePart] = dateStr.split(" ");
  if (!datePart || !timePart) return null;

  const [day, month, year] = datePart.split("/");
  return new Date(`20${year}-${month}-${day}T${timePart}`);
}


    // ✅ Computed Property: Filter Rows with Date & Time Together
    const filteredRows = computed(() => {
  return rows.value.filter(row => {
    if (!row.timestamp) return false; // Ensure row has a timestamp

    // ✅ Convert "DD/MM/YY HH:MM:SS" into JavaScript DateTime Object
    const rowDateTime = parseDateTime(row.timestamp);
    if (!rowDateTime) return false; // Ignore invalid data

    // ✅ Create DateTime Objects for Filters (User Input)
    const fromDateTime = fromDate.value && fromTime.value
      ? new Date(`${fromDate.value}T${fromTime.value}`)
      : null;

    const toDateTime = toDate.value && toTime.value
      ? new Date(`${toDate.value}T${toTime.value}`)
      : null;

    // ✅ Apply Date & Time Range Filtering
    const isAfterStart = fromDateTime ? rowDateTime >= fromDateTime : true;
    const isBeforeEnd = toDateTime ? rowDateTime <= toDateTime : true;

    // ✅ Apply Category Filtering (Dropdown Selection)
    const matchesCategory = selectedFilterCategory.value
      ? row[selectedFilterCategory.value]?.toString().toLowerCase().includes(selectedFilterValue.value?.toString().toLowerCase() || "")
      : true;

    // ✅ Apply General Search Filtering (Search in All Columns)
    const matchesSearch = search.value
      ? Object.values(row).some(value =>
          value?.toString().toLowerCase().includes(search.value.toLowerCase())
        )
      : true;

    return isAfterStart && isBeforeEnd && matchesCategory && matchesSearch;
  });
});



  // ✅ Export Table to CSV
  function wrapCsvValue(val) {
      let formatted = val !== void 0 && val !== null ? String(val) : "";
      formatted = formatted.split('"').join('""');
      return `"${formatted}"`;
    }

    function exportTable() {
      const content = [
        columns.value.map((col) => wrapCsvValue(col.label)),
      ]
        .concat(
          filteredRows.value.map((row) =>
            columns.value.map((col) => wrapCsvValue(row[col.field])).join(",")
          )
        )
        .join("\r\n");

      const status = exportFile("extracted-transactions.csv", content, "text/csv");
      if (status !== true) {
        $q.notify({
          message: "Browser denied file download...",
          color: "negative",
          icon: "warning",
        });
      }
    }


    function resetFilters() {
      fromDate.value = "";
      toDate.value = "";
      fromTime.value = "";
      toTime.value = "";
      selectedFilterCategory.value = null;
      selectedFilterValue.value = null;
      search.value = "";
    }

    return { 
      filterDropdownOptions,
      updateFilterValues,
      files, 
      columns, 
      rows, 
      search, 
      fromDate, 
      toDate, 
      fromTime, 
      toTime, 
      filteredRows,
      exportTable, 
      uploadAndProcessFiles, 
      loading, 
      filterCategories, 
      selectedFilterCategory, 
      selectedFilterValue, 
      dynamicFilterOptions, 
      isDropdownFilter, 
      resetFilters,
      parseDateTime,
      removeFile };
  },
};
</script>
