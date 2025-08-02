<template>
  <div class="q-pa-md">
    <q-layout view="hHh lpR fFf">
      <div class="row justify-end ">
  <div class="col-auto row items-center q-mr-md">
    <q-btn 
      color="primary" 
      icon-right="archive" 
      label="Export to CSV" 
      no-caps 
      @click="exportTable" 
    />
    <div class="q-ml-md text-subtitle1">
      Total Records: {{ filteredRows.length }}
    </div>
  </div>
</div>
      <q-page-container>
    

        <q-page class="">
          <div class="">
            <q-card-section>
              <div class="row ">
                
                <!-- Left Section: File Upload & Process Data -->
                 <!-- Drawer Toggle Button on the right edge -->
                 <!-- <q-btn
                  round
                  dense
                  unelevated
                  class="drawer-toggle-btn"
                  :icon="drawer ? 'chevron_left' : 'chevron_right'"
                  color="primary"
                  @click="drawer = !drawer"
                  :style="{ left: drawer ? '300px' : '0px' }"
                /> -->
                <q-btn
  dense
  unelevated
  class="drawer-toggle-btn"
  :icon="drawer ? 'chevron_left' : 'chevron_right'"
  label="Upload files"
  color="primary"
  @click="drawer = !drawer"
  :style="{ left: drawer ? '300px' : '0px', height: '32px', padding: '0 8px', marginLeft: '38px' }"
/>





                <!-- Left Drawer -->
                <q-drawer
                  v-model="drawer"
                  side="left"
                  behavior="mobile"
                  bordered
                  :width="300"
                >
                  <q-scroll-area class="fit q-pa-md">
                    <div class="text-h6 q-mb-md">Upload Files</div>

                    <q-file
                      v-model="files"
                      label="Upload "
                      filled
                      multiple
                      class="q-mb-md"
                    >
                     
                      <template v-slot:selected>
                        
                      </template>
                    </q-file>


                    <q-card v-if="files.length" class="q-mb-md">
                      <q-card-section>
                        <div class="text-subtitle1">Selected Files:</div>
                        <div style="max-height: 400px; overflow-y: auto;">
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
                        </div>
                      </q-card-section>
                    </q-card>

                    <q-btn
                      color="primary"
                      label="Process Data"
                      class="full-width"
                      icon="play_arrow"
                      no-caps
                      :disable="files.length === 0"
                      @click="uploadAndProcessFiles"
                />
                  </q-scroll-area>
                </q-drawer>

                <!-- Right Section: Filters & Table -->
                <div class="col-md-12 col-xs-12">
                  <div class="row q-mb-md q-mt-md">
                    
                    <!-- Date & Time Filters -->
                     <!-- Date & Time Filters (Combined Date-Time) -->
                    <q-input v-model="fromDate" label="From Date" type="date" dense filled class="col-md-3 col-xs-12 q-pa-xs" />
                    <q-input v-model="fromTime" label="From Time" type="time" dense filled class="col-md-3 col-xs-12 q-pa-xs" />
                    <q-input v-model="toDate" label="To Date" type="date" dense filled class="col-md-3 col-xs-12 q-pa-xs" />
                    <q-input v-model="toTime" label="To Time" type="time" dense filled class="col-md-3 col-xs-12 q-pa-xs" />

                    <!-- Filter Category Dropdown -->
                    <q-select 
                    v-model="selectedFilterCategory" 
                    :options="filterCategories"
                    label="Filter By" 
                    dense 
                    filled 
                    class="col-md-3 col-xs-12 q-pa-xs"
                    emit-value
                    map-options
                    clearable
                    menu-anchor="bottom left"  
                    menu-self="top left"    
                    behavior="menu"
                    @update:model-value="updateFilterValues"
                  />


                    <!-- Dynamic Value Dropdown/Input -->
                    <q-select 
                      v-if="isDropdownFilter"
                      v-model="selectedFilterValue"
                      :options="dynamicFilterOptions"
                      label="Select Value"
                      dense 
                      filled
                      class="col-md-3 col-xs-12 q-pa-xs"
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
                      class="col-md-3 col-xs-12 q-pa-xs"
                    />

                    <!-- Transaction Type Filter -->
                    <q-select
                      v-model="transactionTypeFilter"
                      :options="transactionTypes"
                      label="Transaction Type"
                      dense
                      filled
                      clearable
                      class="col-md-3 col-xs-12 q-pa-xs"
                      emit-value
                      map-options
                    />

                    <!-- Reset Button -->
                    <q-btn 
                      color="primary" 
                      label="Reset"
                      class="q-ml-md"
                      dense
                      style="height: 38px; padding: 0 10px; margin-top: 4px;"
                      @click="resetFilters"
                   
                    />

                  </div>

                  <!-- Loading Indicator -->
                  <q-inner-loading :showing="loading" class="z-max">
                    <q-spinner-gears size="50px" color="primary" />
                  </q-inner-loading>

                  <!-- Search Input & Export -->
                  <div class="row items-center q-mb-md justify-between">
  <!-- Left side: Search -->
  <div class="col-auto">
    <q-input
    rounded 
    outlined
      dense
      debounce="300"
      v-model="search"
      placeholder="Search..."
      input-style="color: #000000;"
      style="width: 900px;"
      color="primary"
   
      class="text-white" 
      
    />
  </div>

  <!-- Right side: Export + Total Records -->
  <!-- <div class="col-auto row items-center">
    <q-btn 
      color="primary" 
      icon-right="archive" 
      label="Export to CSV" 
      no-caps 
      @click="exportTable" 
    />
    <div class="q-ml-md text-subtitle1">
      Total Records: {{ filteredRows.length }}
    </div>
  </div> -->
</div>


                  <!-- Transaction Table -->
                  <q-table
                    flat
                    bordered
                    title="Extracted Transaction Data"
                    :rows="filteredRows"
                    :columns="columns"
                    row-key="transaction_id"
                    v-model:pagination="pagination"
                    :loading="loading"
                    :filter="search"
                    class="sticky-header-table"
                  >
                    <!-- <template v-slot:body-cell-transaction_number="props">
                      <q-td :props="props">
                        <q-btn 
                          flat 
                          dense 
                          color="primary"
                          @click="showTransactionLog(props.row)"  
                        >
                          {{ props.row.transaction_number || 'N/A' }}
                        </q-btn>
                      </q-td>
                    </template> -->
                    <template v-slot:body-cell-stan="props">
                      <q-td :props="props">
                        <q-btn 
                          flat 
                          dense 
                          color="primary"
                          @click="showTransactionLog(props.row)"  
                        >
                          {{ props.row.stan || 'N/A' }}
                        </q-btn>
                      </q-td>
                    </template>

                    <template v-slot:body-cell-amount="props">
                      <q-td :props="props">
                        <span :class="{'text-green': props.row.transaction_type === 'Deposit', 
                                      'text-negative': props.row.transaction_type === 'Withdrawal'}">
                          {{ formatCurrency(props.row.amount) }}
                        </span>
                      </q-td>
                    </template>

                    <template v-slot:body-cell-transaction_type="props">
                      <q-td :props="props">
                        <q-chip 
                          :color="props.row.transaction_type === 'Deposit' ? 'green' : 
                                  props.row.transaction_type === 'Withdrawal' ? 'orange' : 'grey'"
                          text-color="white"
                          size="sm"
                          dense
                        >
                          {{ props.row.transaction_type || 'Unknown' }}
                        </q-chip>
                      </q-td>
                    </template>

                    <template v-slot:body-cell-response_code="props">
                      <q-td :props="props">
                        <q-badge 
                          :color="props.row.response_code === '000' ? 'green' : 
                                  props.row.response_code === '100' ? 'orange' : 'red'"
                        >
                          {{ props.row.response_code || 'N/A' }}
                        </q-badge>
                      </q-td>
                    </template>

                    <template v-slot:body-cell-status="props">
                      <q-td :props="props">
                        <span>{{ props.row.status || 'No Status' }}</span>
                      </q-td>
                    </template>

                    <template v-slot:body-cell-card_number="props">
                      <q-td :props="props">
                        {{ formatCardNumber(props.row.card_number) }}
                      </q-td>
                    </template>
                    
                    <template v-slot:body-cell-retract="props">
                      <q-td :props="props">
                        <q-badge :color="props.row.retract === 'Yes' ? 'red' : 'green'">
                          {{ props.row.retract || 'N/A' }}
                        </q-badge>
                      </q-td>
                    </template>
                  </q-table>


                </div>
              </div>
            </q-card-section>
          </div>
        </q-page>

        <!-- EJ Log Popup Dialog -->
        <q-dialog v-model="isDialogOpen">
            <q-card style="width: 800px; max-width: 100vw;">
              <q-card-section>
                <div class="text-h6">EJ Log Data</div>
              </q-card-section>

              <q-separator />

              <q-card-section style="max-height: 400px; overflow-y: auto;">
                <pre v-if="selectedTransactionLog && selectedTransactionLog.length > 0">{{ selectedTransactionLog }}</pre>
                <div v-else>No EJ log available.</div>
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
import { nextTick } from "vue";

export default {
  setup() {
    const $q = useQuasar();
    const files = ref([]);
    const search = ref("");
    const fromDate = ref("");
    const toDate = ref("");
    const fromTime = ref("");
    const toTime = ref("");
    const rows = ref([]); 
    const loading = ref(false);
    const selectedFilterCategory = ref(null);
    const selectedFilterValue = ref(null);
    const isDialogOpen = ref(false);
    const selectedTransactionLog = ref("");
    const transactionTypeFilter = ref(null);
    const collapsed = ref(false); // Start expanded or set to true for collapsed default
    //const drawer = ref(false);
    const drawer = ref(false);

    const selectedRowId = ref(null);

    const pagination = ref({
      sortBy: 'timestamp',
      descending: true,
      page: 1,
      rowsPerPage: 7
    });
   
    // Function to remove a file from the list
    const removeFile = (index) => {
      files.value.splice(index, 1);
    };

    // List of possible transaction types
    const transactionTypes = [
      { label: 'Withdrawal', value: 'Withdrawal' },
      { label: 'Deposit', value: 'Deposit' },
      { label: 'Balance Inquiry', value: 'Balance Inquiry' },
      { label: 'Transfer', value: 'Transfer' },
    ];

    // Format currency to display with BDT symbol
    const formatCurrency = (amount) => {
      if (!amount) return 'N/A';
      const amountNum = parseFloat(amount);
      if (isNaN(amountNum)) return 'N/A';
      return `BDT ${amountNum.toLocaleString()}`;
    };

    // Format card number with proper masking
    const formatCardNumber = (cardNumber) => {
      if (!cardNumber) return 'N/A';
      return cardNumber;  // Already masked in the data
    };

    // ✅ Table Columns
    const columns = ref([
  { name: "timestamp", label: "Timestamp", field: "timestamp", sortable: true },
  { name: "transaction_id", label: "Transaction ID", field: "transaction_id", sortable: true },
  { name: "card_number", label: "Card Number", field: "card_number", sortable: true },
  { name: "transaction_type", label: "Transaction Type", field: "transaction_type", sortable: true },
  { name: "amount", label: "Amount", field: "amount", sortable: true },
  { name: "response_code", label: "Response Code", field: "response_code", sortable: true },
  { name: "account_number", label: "Account Number", field: "account_number", sortable: true },
  { name: "terminal", label: "Terminal", field: "terminal", sortable: true },
  { name: "transaction_number", label: "Transaction Number", field: "transaction_number", sortable: true },
  { name: "stan", label: "STAN", field: "stan", sortable: true },
  { name: "file_name", label: "File Name", field: "file_name", sortable: true },

  // Flags & status
  { name: "scenario", label: "Scenario", field: "scenario", sortable: true },
  { name: "pin_entry", label: "PIN Entry", field: "pin_entry", sortable: true },
  { name: "retract", label: "Retract", field: "retract", sortable: true },
  { name: "no_notes_dispensed", label: "No Notes Dispensed", field: "no_notes_dispensed", sortable: true },
  { name: "notes_dispensed_unknown", label: "Notes Dispensed Unknown", field: "notes_dispensed_unknown", sortable: true },
  { name: "notes_dispensed", label: "Notes Dispensed", field: "notes_dispensed", sortable: true },
  { name: "status", label: "Status", field: "status", sortable: true },
  { name: "result", label: "Result", field: "result", sortable: true },

  // Dispensed breakdown
  { name: "dispensed_t1", label: "Dispensed T1", field: "dispensed_t1", sortable: true },
  { name: "dispensed_t2", label: "Dispensed T2", field: "dispensed_t2", sortable: true },
  { name: "dispensed_t3", label: "Dispensed T3", field: "dispensed_t3", sortable: true },
  { name: "dispensed_t4", label: "Dispensed T4", field: "dispensed_t4", sortable: true },

  // Total dispensed/rejected/remaining
  { name: "cash_dispensed", label: "Cash Dispensed", field: "cash_dispensed", sortable: true },
  { name: "cash_rejected", label: "Cash Rejected", field: "cash_rejected", sortable: true },
  { name: "cash_remaining", label: "Cash Remaining", field: "cash_remaining", sortable: true },

  // Note counts and types
  { name: "Note_Count_BDT500", label: "Note Count BDT500", field: "Note_Count_BDT500", sortable: true },
  { name: "Note_Count_BDT1000", label: "Note Count BDT1000", field: "Note_Count_BDT1000", sortable: true },
  { name: "Number of Total Inserted Notes", label: "Total Inserted Notes", field: "Number of Total Inserted Notes", sortable: true },

  // Denominations - BDT 500
  { name: "BDT500_ABOX", label: "BDT500 ABOX", field: "BDT500_ABOX", sortable: true },
  { name: "BDT500_TYPE1", label: "BDT500 TYPE1", field: "BDT500_TYPE1", sortable: true },
  { name: "BDT500_TYPE2", label: "BDT500 TYPE2", field: "BDT500_TYPE2", sortable: true },
  { name: "BDT500_TYPE3", label: "BDT500 TYPE3", field: "BDT500_TYPE3", sortable: true },
  { name: "BDT500_TYPE4", label: "BDT500 TYPE4", field: "BDT500_TYPE4", sortable: true },
  { name: "BDT500_RETRACT", label: "BDT500 RETRACT", field: "BDT500_RETRACT", sortable: true },
  { name: "BDT500_REJECT", label: "BDT500 REJECT", field: "BDT500_REJECT", sortable: true },
  { name: "BDT500_RETRACT2", label: "BDT500 RETRACT2", field: "BDT500_RETRACT2", sortable: true },

  // Denominations - BDT 1000
  { name: "BDT1000_ABOX", label: "BDT1000 ABOX", field: "BDT1000_ABOX", sortable: true },
  { name: "BDT1000_TYPE1", label: "BDT1000 TYPE1", field: "BDT1000_TYPE1", sortable: true },
  { name: "BDT1000_TYPE2", label: "BDT1000 TYPE2", field: "BDT1000_TYPE2", sortable: true },
  { name: "BDT1000_TYPE3", label: "BDT1000 TYPE3", field: "BDT1000_TYPE3", sortable: true },
  { name: "BDT1000_TYPE4", label: "BDT1000 TYPE4", field: "BDT1000_TYPE4", sortable: true },
  { name: "BDT1000_RETRACT", label: "BDT1000 RETRACT", field: "BDT1000_RETRACT", sortable: true },
  { name: "BDT1000_REJECT", label: "BDT1000 REJECT", field: "BDT1000_REJECT", sortable: true },
  { name: "BDT1000_RETRACT2", label: "BDT1000 RETRACT2", field: "BDT1000_RETRACT2", sortable: true },

  // Totals
  { name: "TOTAL_ABOX", label: "Total ABOX", field: "TOTAL_ABOX", sortable: true },
  { name: "TOTAL_TYPE1", label: "Total Type 1", field: "TOTAL_TYPE1", sortable: true },
  { name: "TOTAL_TYPE2", label: "Total Type 2", field: "TOTAL_TYPE2", sortable: true },
  { name: "TOTAL_TYPE3", label: "Total Type 3", field: "TOTAL_TYPE3", sortable: true },
  { name: "TOTAL_TYPE4", label: "Total Type 4", field: "TOTAL_TYPE4", sortable: true },
  { name: "TOTAL_RETRACT", label: "Total Retract", field: "TOTAL_RETRACT", sortable: true },
  { name: "TOTAL_REJECT", label: "Total Reject", field: "TOTAL_REJECT", sortable: true },
  { name: "TOTAL_RETRACT2", label: "Total Retract2", field: "TOTAL_RETRACT2", sortable: true },

  // Unknown
  { name: "UNKNOWN_TYPE4", label: "Unknown Type 4", field: "UNKNOWN_TYPE4", sortable: true },
  { name: "UNKNOWN_RETRACT", label: "Unknown Retract", field: "UNKNOWN_RETRACT", sortable: true },
  { name: "UNKNOWN_REJECT", label: "Unknown Reject", field: "UNKNOWN_REJECT", sortable: true },
  { name: "UNKNOWN_RETRACT2", label: "Unknown Retract2", field: "UNKNOWN_RETRACT2", sortable: true },

  // "retract_type1": None,
  //           "retract_type2": None,
  //           "retract_type3": None,
  //           "retract_type4": None,
  //           "total_retracted_notes": None,
  { name: "retract_type1", label: "WD Retracted T1", field: "retract_type1", sortable: true },
  { name: "retract_type2", label: "WD Retracted T2", field: "retract_type2", sortable: true },
  { name: "retract_type3", label: "WD Retracted T3", field: "retract_type3", sortable: true },
  { name: "retract_type4", label: "WD Retracted T4", field: "retract_type4", sortable: true },
  { name: "total_retracted_notes", label: "Total WD Retracted Notes", field: "total_retracted_notes", sortable: true },

//   "deposit_retract_100": None,
// "deposit_retract_500": None,
// "deposit_retract_1000": None,
// "deposit_retract_unknown": None,
// "total_deposit_retracted": None,
  { name: "deposit_retract_100", label: "Deposit Retracted BDT100", field: "deposit_retract_100", sortable: true },
  { name: "deposit_retract_500", label: "Deposit Retracted BDT500", field: "deposit_retract_500", sortable: true },
  { name: "deposit_retract_1000", label: "Deposit Retracted BDT1000", field: "deposit_retract_1000", sortable: true },
  { name: "deposit_retract_unknown", label: "Deposit Retracted Unknown", field: "deposit_retract_unknown", sortable: true },
  { name: "total_deposit_retracted", label: "Total Deposit Retracted Notes", field: "total_deposit_retracted", sortable: true },

]);

    // Available Filter Categories - Updated to match API JSON fields
    const filterCategories = ref([
      { label: "STAN", value: "stan" },
      { label: "Card Number", value: "card_number" },
      { label: "Amount", value: "amount" },
      { label: "Response Code", value: "response_code" },
      { label: "Terminal", value: "terminal" },
      { label: "Status", value: "status" },
      { label: "File Name", value: "file_name" },
      { label: "Retract", value: "retract" },
      { label: "Account Number", value: "account_number" },
      { label: "Total Notes", value: "Number_of_Total_Inserted_Notes" },
      { label: "Scenario", value: "scenario" },
    ]);

    const allFilterOptions = ref([]);  // Stores all options for the selected filter
    const dynamicFilterOptions = ref([]);  // Stores filtered dropdown options

    // Function to update filter values when filter category changes
    function updateFilterValues() {
      selectedFilterValue.value = null;
      if (!selectedFilterCategory.value) {
        allFilterOptions.value = [];
        dynamicFilterOptions.value = [];
        return;
      }

      const field = selectedFilterCategory.value;
      const uniqueValues = new Set(rows.value.map(row => row[field]).filter(val => val));
      allFilterOptions.value = Array.from(uniqueValues).map(val => ({ label: val, value: val })).sort((a, b) => {
        if (typeof a.label === 'string' && typeof b.label === 'string') {
          return a.label.localeCompare(b.label);
        }
        return a.label - b.label;
      });
      dynamicFilterOptions.value = [...allFilterOptions.value];
    }

    // Function to filter dropdown options based on input
    function filterDropdownOptions(val, update) {
      if (!val) {
        update(() => {
          dynamicFilterOptions.value = [...allFilterOptions.value];
        });
        return;
      }

      update(() => {
        dynamicFilterOptions.value = allFilterOptions.value.filter(option =>
          option.label?.toString().toLowerCase().includes(val.toLowerCase())
        );
      });
    }

    // Check if the filter category should use a dropdown
    const isDropdownFilter = computed(() => selectedFilterCategory.value && allFilterOptions.value.length > 0);

    // Upload and Process Files
    async function uploadAndProcessFiles() {
      
      if (files.value.length === 0) {
        $q.notify({
          color: 'negative',
          message: 'Please select at least one file.',
          icon: 'warning'
        });
        return;
      }
      // 👇 Close the drawer right after clicking Process
      drawer.value = false;
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
          updateFilterValues();
          
          $q.notify({
            color: 'positive',
            message: `Processed ${rows.value.length} transactions successfully`,
            icon: 'check_circle'
          });
        } else {
          rows.value = [];
          $q.notify({
            color: 'warning',
            message: 'No transactions found in the files',
            icon: 'info'
          });
        }
      } catch (error) {
        console.error("❌ API call failed:", error);
        $q.notify({
          color: 'negative',
          message: 'Failed to process files. Please check server connection.',
          icon: 'error'
        });
      } finally {
        loading.value = false;
      }
    }
    
    // Function to show transaction log details
    function showTransactionLog(row) {
      console.log("Selected Row:", row);
      if (row && Array.isArray(row.ej_log) && row.ej_log.length > 0) {
        selectedTransactionLog.value = row.ej_log.join("\n");
        console.log("EJ Log Found:", selectedTransactionLog.value);

        // Ensure Vue updates before opening the dialog
        nextTick(() => {
          isDialogOpen.value = true;
        });
      } else {
        selectedTransactionLog.value = "No EJ log available.";
        console.log("No EJ log found!");
        isDialogOpen.value = true;
      }
    }

    // Function to Convert "DD/MM/YY HH:MM:SS" or "DD-MM-YY HH:MM:SS" → JavaScript Date
    function parseDateTime(dateStr) {
      if (!dateStr) return null;

      // Handle different date formats
      let parts;
      if (dateStr.includes('-')) {
        // Handle format "DD-MM-YY HH:MM:SS"
        parts = dateStr.split(' ');
        if (parts.length !== 2) return null;
        
        const [day, month, year] = parts[0].split('-');
        if (!day || !month || !year) return null;
        return new Date(`20${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}T${parts[1]}`);
      } else if (dateStr.includes('/')) {
        // Handle format "DD/MM/YY HH:MM:SS"
        parts = dateStr.split(' ');
        if (parts.length !== 2) return null;
        
        const [day, month, year] = parts[0].split('/');
        if (!day || !month || !year) return null;
        return new Date(`20${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}T${parts[1]}`);
      }

      return null;
    }

    // Computed Property: Filter Rows with Date & Time Together
    const filteredRows = computed(() => {
      return rows.value.filter(row => {
        if (!row.timestamp) return false;

        // Convert timestamp into JavaScript DateTime Object
        const rowDateTime = parseDateTime(row.timestamp);
        if (!rowDateTime) return false;

        // Create DateTime Objects for Filters (User Input)
        const fromDateTime = fromDate.value && fromTime.value
          ? new Date(`${fromDate.value}T${fromTime.value}`)
          : null;

        const toDateTime = toDate.value && toTime.value
          ? new Date(`${toDate.value}T${toTime.value}`)
          : null;

        // Apply Date & Time Range Filtering
        const isAfterStart = fromDateTime ? rowDateTime >= fromDateTime : true;
        const isBeforeEnd = toDateTime ? rowDateTime <= toDateTime : true;

        // Apply Category Filtering (Dropdown Selection)
        const matchesCategory = selectedFilterCategory.value && selectedFilterValue.value
          ? row[selectedFilterCategory.value]?.toString().toLowerCase().includes(selectedFilterValue.value?.toString().toLowerCase() || "")
          : true;

        // Apply Transaction Type Filtering
        const matchesTransactionType = transactionTypeFilter.value
          ? row.transaction_type === transactionTypeFilter.value
          : true;

        // Apply General Search Filtering (Search in All Columns)
        const matchesSearch = search.value
          ? Object.values(row).some(value =>
              value?.toString().toLowerCase().includes(search.value.toLowerCase())
            )
          : true;

        return isAfterStart && isBeforeEnd && matchesCategory && matchesTransactionType && matchesSearch;
      });
    });

    // Export Table to CSV
    function wrapCsvValue(val) {
      if (val === void 0 || val === null) return '""';
      let formatted = String(val);
      formatted = formatted.split('"').join('""');
      return `"${formatted}"`;
    }

    function exportTable() {
      // Get visible columns only
      const visibleColumns = columns.value;
      
      const content = [
        visibleColumns.map((col) => wrapCsvValue(col.label)),
      ]
        .concat(
          filteredRows.value.map((row) =>
            visibleColumns.map((col) => wrapCsvValue(row[col.field])).join(",")
          )
        )
        .join("\r\n");

      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `atm-transactions-${timestamp}.csv`;
      
      const status = exportFile(filename, content, "text/csv");
      if (status !== true) {
        $q.notify({
          message: "Browser denied file download...",
          color: "negative",
          icon: "warning",
        });
      } else {
        $q.notify({
          message: "Export successful",
          color: "positive",
          icon: "check_circle",
        });
      }
    }

    // Reset all filters
    function resetFilters() {
      fromDate.value = "";
      toDate.value = "";
      fromTime.value = "";
      toTime.value = "";
      selectedFilterCategory.value = null;
      selectedFilterValue.value = null;
      transactionTypeFilter.value = null;
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
      removeFile,
      isDialogOpen,
      selectedTransactionLog,
      showTransactionLog,
      transactionTypeFilter,
      transactionTypes,
      formatCurrency,
      formatCardNumber,
      pagination,
      collapsed,
      drawer,
      selectedRowId
    };
  },
};
</script>

<style scoped>
.q-table__bottom {
  padding-top: 8px;
}

/* Additional styling for better readability */
.q-table thead tr {
  background: #f5f5f5;
}

.q-table tbody tr:hover {
  background-color: #f0f8ff !important;
}

/* Style for dialog pre block */
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-size: 0.9em;
}

.drawer-toggle {
  position: absolute;
  top: 50%;
  right: -16px; 
  transform: translateY(-50%);
  z-index: 1000;
}

.drawer-toggle-btn {
  position: fixed;
  top: 10%;
  left: 300px; /* Same as drawer width */
  transform: translateY(-50%);
  z-index: 1001;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.2);
}


</style>
