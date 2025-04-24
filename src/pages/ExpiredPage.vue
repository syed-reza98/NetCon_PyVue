<template>
    <q-dialog v-model="showTrialDialog" persistent>
      <q-card>
        <q-card-section class="bg-red text-white">
          <div class="text-h6">Trial Expired</div>
        </q-card-section>
  
        <q-card-section>
          Your free trial has ended. Please upgrade your plan to continue using the app.
        </q-card-section>
  
        <q-card-actions align="right">
          <q-btn flat label="Upgrade" color="primary" @click="goToUpgrade" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </template>
  
  
  <script>
  export default {
    data () {
      return {
        showTrialDialog: false
      }
    },
    mounted () {
      // Show trial dialog on page load
      this.showTrialDialog = true
    },
    methods: {
      goToUpgrade () {
        window.location.href = '/'
      }
    }
  }
  </script>
  
  