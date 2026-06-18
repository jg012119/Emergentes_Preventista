document.addEventListener('DOMContentLoaded', () => {
  // Navigation State
  let currentSlideIndex = 0;
  const slides = document.querySelectorAll('.slide');
  const dotsContainer = document.querySelector('.progress-indicator');
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');

  // Create Navigation Dots
  slides.forEach((_, index) => {
    const dot = document.createElement('div');
    dot.classList.add('progress-dot');
    if (index === 0) dot.classList.add('active');
    dot.addEventListener('click', () => goToSlide(index));
    dotsContainer.appendChild(dot);
  });

  const dots = document.querySelectorAll('.progress-dot');

  // Usability chart bars elements (Slide 7 animation)
  const barBo = document.querySelector('.chart-bar-inner.success');
  const barUs = document.querySelector('.chart-bar-inner.danger');
  const barGlobal = document.querySelector('.chart-bar-inner.warning');

  // Set initial width to 0 for animation
  if (barBo) barBo.style.width = '0%';
  if (barUs) barUs.style.width = '0%';
  if (barGlobal) barGlobal.style.width = '0%';

  // Navigation Functions
  function updateSlides() {
    slides.forEach((slide, index) => {
      slide.classList.remove('active', 'previous');
      if (index === currentSlideIndex) {
        slide.classList.add('active');
      } else if (index < currentSlideIndex) {
        slide.classList.add('previous');
      }
    });

    dots.forEach((dot, index) => {
      dot.classList.toggle('active', index === currentSlideIndex);
    });

    // Update buttons visibility/state
    prevBtn.style.opacity = currentSlideIndex === 0 ? '0.3' : '1';
    prevBtn.style.pointerEvents = currentSlideIndex === 0 ? 'none' : 'auto';
    
    nextBtn.style.opacity = currentSlideIndex === slides.length - 1 ? '0.3' : '1';
    nextBtn.style.pointerEvents = currentSlideIndex === slides.length - 1 ? 'none' : 'auto';

    // Trigger Usability Chart Animation (Slide Index 6)
    if (currentSlideIndex === 6) {
      setTimeout(() => {
        if (barBo) barBo.style.width = '79.4%';
        if (barUs) barUs.style.width = '36.6%';
        if (barGlobal) barGlobal.style.width = '58.6%';
      }, 300);
    } else {
      if (barBo) barBo.style.width = '0%';
      if (barUs) barUs.style.width = '0%';
      if (barGlobal) barGlobal.style.width = '0%';
    }
  }

  function goToSlide(index) {
    if (index >= 0 && index < slides.length) {
      currentSlideIndex = index;
      updateSlides();
    }
  }

  function nextSlide() {
    if (currentSlideIndex < slides.length - 1) {
      currentSlideIndex++;
      updateSlides();
    }
  }

  function prevSlide() {
    if (currentSlideIndex > 0) {
      currentSlideIndex--;
      updateSlides();
    }
  }

  // Event Listeners
  nextBtn.addEventListener('click', nextSlide);
  prevBtn.addEventListener('click', prevSlide);

  // Keyboard Navigation
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === ' ') {
      // Prevent spacebar scrolling page when slide deck is open
      if (e.key === ' ') e.preventDefault();
      nextSlide();
    } else if (e.key === 'ArrowLeft') {
      prevSlide();
    }
  });

  // Swipe Support
  let touchStartX = 0;
  let touchEndX = 0;

  document.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
  }, false);

  document.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
  }, false);

  function handleSwipe() {
    const swipeThreshold = 50;
    if (touchEndX < touchStartX - swipeThreshold) {
      nextSlide();
    }
    if (touchEndX > touchStartX + swipeThreshold) {
      prevSlide();
    }
  }

  // Interactive Chat Simulator Logic (AJE Mobile App replica)
  const chatArea = document.getElementById('chat-area');
  const demoButtons = document.querySelectorAll('.demo-phrase-btn');
  const phoneMicBtn = document.getElementById('phone-mic-btn');
  const phoneBtnIcon = document.getElementById('phone-btn-icon');
  const phoneInput = document.getElementById('phone-input');
  const voiceBar = document.getElementById('voice-bar');
  const voiceText = document.getElementById('voice-text');
  let simulationActive = false;

  const chatFlows = {
    rules: {
      userText: "Quiero 4 Big Cola de 2 litros y 2 Volt para el viernes.",
      agentText: "¡Listo! Ya armé el borrador de tu pedido por un total de Bs. 56.00. Por favor, revísalo en tu pantalla y presiona confirmar para agendar su despacho.",
      action: {
        type: "confirm_order",
        order_id: "AJE-9823",
        label: "Confirmar y enviar a AJE",
        store: "Tienda San Miguel",
        status: "borrador",
        total: "Bs. 56.00",
        delivery: "Viernes"
      }
    },
    llm: {
      userText: "sielito el más pequeñito me mandas porfa dos y un cifrut",
      agentText: "*(Interpretación contextual — Modelo local)* Entiendo tu mensaje en lenguaje natural. He mapeado los sinónimos y he preparado este borrador:",
      action: {
        type: "confirm_order",
        order_id: "AJE-9824",
        label: "Confirmar y enviar a AJE",
        store: "Tienda San Miguel",
        status: "borrador",
        total: "Bs. 7.00",
        delivery: "Hoy"
      }
    },
    reject: {
      userText: "quiero una docena de chelas bien frías y 2 big cola",
      agentText: "*(Validación del catálogo)* Lo sentimos, no distribuimos alcohol ni snacks. He filtrado los artículos no válidos y agregué el resto al borrador:",
      action: {
        type: "confirm_order",
        order_id: "AJE-9825",
        label: "Confirmar y enviar a AJE",
        store: "Tienda San Miguel",
        status: "borrador",
        total: "Bs. 20.00",
        delivery: "Hoy"
      }
    }
  };

  demoButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      if (simulationActive) return;
      
      const type = btn.getAttribute('data-type');
      if (chatFlows[type]) {
        runVoiceSimulation(chatFlows[type]);
      }
    });
  });

  function runVoiceSimulation(flow) {
    simulationActive = true;
    
    // Reset inputs
    phoneInput.value = '';
    
    // 1. Simulate Voice recording (starts speaking)
    phoneMicBtn.classList.add('active');
    phoneBtnIcon.setAttribute('name', 'stop');
    voiceBar.style.display = 'flex';
    voiceText.textContent = 'Escuchando pedido...';
    
    // 2. Type transcript slowly
    let currentText = '';
    const words = flow.userText.split(' ');
    let wordIndex = 0;
    
    const typeInterval = setInterval(() => {
      if (wordIndex < words.length) {
        currentText += (wordIndex === 0 ? '' : ' ') + words[wordIndex];
        phoneInput.value = currentText;
        wordIndex++;
      } else {
        clearInterval(typeInterval);
        
        // Voice finish
        setTimeout(() => {
          phoneMicBtn.classList.remove('active');
          phoneBtnIcon.setAttribute('name', 'send');
          voiceText.textContent = 'Listo, interpretando...';
          
          setTimeout(() => {
            voiceBar.style.display = 'none';
            phoneInput.value = '';
            phoneBtnIcon.setAttribute('name', 'mic');
            
            // Append User message to list
            appendMessage(flow.userText, 'user');
            
            // Show Typing indicator for Agent
            setTimeout(() => {
              const typingBubble = appendMessage('Escribiendo...', 'agent typing');
              
              // Agent reply
              setTimeout(() => {
                typingBubble.remove();
                appendMessageWithAction(flow.agentText, flow.action);
                simulationActive = false;
              }, 1200);
              
            }, 800);
            
          }, 800);
        }, 500);
      }
    }, 1500 / words.length); // complete user typing in ~1.5s
  }

  function appendMessage(text, sender) {
    const bubble = document.createElement('div');
    bubble.className = `phone-bubble ${sender}`;
    
    const bubbleText = document.createElement('div');
    bubbleText.className = 'phone-bubble-text';
    bubbleText.textContent = text;
    
    const bubbleMeta = document.createElement('div');
    bubbleMeta.className = 'phone-bubble-meta';
    
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    bubbleMeta.textContent = `${hours}:${minutes}`;
    
    bubble.appendChild(bubbleText);
    bubble.appendChild(bubbleMeta);
    
    // Add to list (inverted UI container, prepend to top)
    chatArea.insertBefore(bubble, chatArea.firstChild);
    chatArea.scrollTop = chatArea.scrollHeight;
    
    return bubble;
  }

  function appendMessageWithAction(text, actionData) {
    const bubble = document.createElement('div');
    bubble.className = 'phone-bubble agent';
    
    const bubbleText = document.createElement('div');
    bubbleText.className = 'phone-bubble-text';
    bubbleText.textContent = text;
    
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    const bubbleMeta = document.createElement('div');
    bubbleMeta.className = 'phone-bubble-meta';
    bubbleMeta.textContent = `${hours}:${minutes}`;
    
    bubble.appendChild(bubbleText);
    
    // Create Actions Wrapper
    const actionsWrapper = document.createElement('div');
    actionsWrapper.className = 'phone-message-actions';
    
    const actionBtn = document.createElement('div');
    actionBtn.className = 'phone-message-action';
    
    const iconName = actionData.type === 'confirm_order' ? 'checkmark-circle-outline' : 'receipt-outline';
    const metaText = `${actionData.store} - ${actionData.status} - ${actionData.total} - Entrega ${actionData.delivery}`;
    
    actionBtn.innerHTML = `
      <div class="phone-action-icon-wrap">
        <ion-icon name="${iconName}"></ion-icon>
      </div>
      <div class="phone-action-copy">
        <div class="phone-action-title">${actionData.label}</div>
        <div class="phone-action-meta">${metaText}</div>
      </div>
      <ion-icon name="chevron-forward" style="color: #b8acd8; font-size: 14px;"></ion-icon>
    `;
    
    // Action event handler (replica of confirmOrder inside app)
    actionBtn.addEventListener('click', () => {
      if (confirm(`Confirmar pedido ${actionData.order_id}\n\nEl pedido pasará a Pendiente y será enviado a AJE.`)) {
        actionBtn.style.pointerEvents = 'none';
        actionBtn.style.opacity = '0.5';
        
        setTimeout(() => {
          // Add system message
          const confText = `Pedido #${actionData.order_id} confirmado y enviado a AJE. Estado: Pendiente.`;
          appendMessage(confText, 'agent');
          
          // Update order status in web dashboard array
          const matchedOrder = mockOrders.find(o => o.id === actionData.order_id);
          if (matchedOrder) {
            matchedOrder.status = 'pendiente';
            loadPanelTable();
            updateDashboardStats();
          }
          
          alert('¡Pedido enviado a AJE Bolivia! Se ha enviado una notificación de confirmación al correo del cliente.');
        }, 500);
      }
    });
    
    actionsWrapper.appendChild(actionBtn);
    bubble.appendChild(actionsWrapper);
    
    // Add Feedback Row
    const feedbackRow = document.createElement('div');
    feedbackRow.className = 'phone-feedback-row';
    feedbackRow.innerHTML = `
      <button class="phone-feedback-btn" title="Me gusta"><ion-icon name="thumbs-up-outline"></ion-icon></button>
      <button class="phone-feedback-btn" title="No me gusta"><ion-icon name="thumbs-down-outline"></ion-icon></button>
    `;
    
    // Handle feedback clicks
    const fBtns = feedbackRow.querySelectorAll('.phone-feedback-btn');
    fBtns.forEach(fBtn => {
      fBtn.addEventListener('click', () => {
        const wasActive = fBtn.classList.contains('active');
        fBtns.forEach(b => b.classList.remove('active'));
        if (!wasActive) fBtn.classList.add('active');
      });
    });
    
    bubble.appendChild(feedbackRow);
    bubble.appendChild(bubbleMeta);
    
    chatArea.insertBefore(bubble, chatArea.firstChild);
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  // Suggestions chips clicks
  window.sendSuggestion = function(suggestion) {
    if (simulationActive) return;
    
    appendMessage(suggestion, 'user');
    
    setTimeout(() => {
      const typingBubble = appendMessage('Escribiendo...', 'agent typing');
      
      setTimeout(() => {
        typingBubble.remove();
        if (suggestion.toLowerCase().includes('pendiente')) {
          appendMessage('Actualmente tienes 2 pedidos PENDIENTES de entrega. Puedes revisarlos en la sección Pedidos.', 'agent');
        } else if (suggestion.toLowerCase().includes('menu') || suggestion.toLowerCase().includes('catálogo')) {
          appendMessage('Nuestro catálogo activo incluye:\n- Big Cola 2L (Bs. 10.00)\n- Agua Cielo 500ml (Bs. 2.00)\n- Volt 300ml (Bs. 8.00)\n- Cifrut 500ml (Bs. 3.00)', 'agent');
        } else {
          appendMessage('Entendido, cargando listado solicitado...', 'agent');
        }
      }, 1000);
    }, 600);
  };

  // Bind suggestion chips clicks from HTML dynamically
  const chips = document.querySelectorAll('.phone-suggestion-chip');
  chips.forEach(chip => {
    chip.removeAttribute('onclick'); // remove inline script
    chip.addEventListener('click', () => {
      sendSuggestion(chip.textContent);
    });
  });

  // Fake microphone button click logic
  phoneMicBtn.addEventListener('click', () => {
    if (simulationActive) return;
    runVoiceSimulation(chatFlows.rules);
  });


  // ── REACT OPERATOR PANEL SIMULATION (Slide 6) ──
  const panelTableBody = document.getElementById('panel-table-body');
  const panelModal = document.getElementById('panel-detail-modal');
  const panelModalClose = document.getElementById('panel-modal-close');
  
  // Modal DOM elements
  const pmId = document.getElementById('pm-id');
  const pmStore = document.getElementById('pm-store');
  const pmTotal = document.getElementById('pm-total');
  const pmStatus = document.getElementById('pm-status');
  const pmDate = document.getElementById('pm-date');
  const pmItems = document.getElementById('pm-items');

  // Real mock orders loaded in dashboard
  const mockOrders = [
    { id: "AJE-9823", store: "Tienda San Miguel", total: "Bs. 56.00", status: "borrador", date: "17/06/2026", items: "Big Cola 2L (x4) / Volt 300ml (x2)" },
    { id: "AJE-9824", store: "Tienda Flores", total: "Bs. 7.00", status: "confirmado", date: "17/06/2026", items: "Agua Cielo 500ml (x2) / Cifrut Botella 500ml (x1)" },
    { id: "AJE-9825", store: "Tienda Sur", total: "Bs. 20.00", status: "rechazado", date: "16/06/2026", items: "Big Cola 2L (x2) / Cerveza Huari (Descargado por reglas de alcohol)" },
    { id: "AJE-9042", store: "Supermercado Fidalga", total: "Bs. 850.00", status: "confirmado", date: "15/06/2026", items: "Volt 300ml Box (x5) / Agua Cielo 1.5L Pack (x4)" },
    { id: "AJE-8911", store: "Restaurante El Prado", total: "Bs. 140.00", status: "en_proceso", date: "14/06/2026", items: "Cifrut Botella 500ml (x24) / Big Cola 500ml (x12)" }
  ];

  // Dynamic Dashboard Stats updates matching Dashboard.jsx
  function updateDashboardStats() {
    let total = 38;
    let pending = 11;
    let confirmed = 23;
    let rejected = 4;
    
    mockOrders.forEach(order => {
      total++;
      if (order.status === 'pendiente') pending++;
      else if (order.status === 'confirmado' || order.status === 'pagado') confirmed++;
      else if (order.status === 'rechazado') rejected++;
    });
    
    const totalEl = document.getElementById('panel-stat-total');
    const pendingEl = document.getElementById('panel-stat-pending');
    const confirmedEl = document.getElementById('panel-stat-confirmed');
    const rejectedEl = document.getElementById('panel-stat-rejected');
    
    if (totalEl) totalEl.textContent = total;
    if (pendingEl) pendingEl.textContent = pending;
    if (confirmedEl) confirmedEl.textContent = confirmed;
    if (rejectedEl) rejectedEl.textContent = rejected;
  }

  // Populate Panel Table
  function loadPanelTable() {
    panelTableBody.innerHTML = '';
    mockOrders.forEach(order => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-family: monospace; color: var(--color-secondary); font-weight: bold;">#${order.id}</td>
        <td>${order.store}</td>
        <td>${order.total}</td>
        <td><span class="panel-badge ${order.status}">${order.status}</span></td>
        <td style="color: var(--color-text-muted);">${order.date}</td>
      `;
      
      // Row click triggers details modal popup
      tr.addEventListener('click', () => {
        pmId.textContent = `Pedido #${order.id}`;
        pmStore.textContent = order.store;
        pmTotal.textContent = order.total;
        
        // Status badge configuration
        pmStatus.textContent = order.status;
        pmStatus.className = `panel-badge ${order.status}`;
        
        pmDate.textContent = order.date;
        pmItems.textContent = order.items;
        
        panelModal.style.display = 'block';
      });
      
      panelTableBody.appendChild(tr);
    });
  }

  // Close modal click handlers
  panelModalClose.addEventListener('click', () => {
    panelModal.style.display = 'none';
  });

  // Load table on start
  loadPanelTable();
  updateDashboardStats();


  // ── ROI SAVINGS CALCULATOR (Slide 8: Physical vs Digital) ──
  const rangeStores = document.getElementById('roi-range-stores');
  const rangeVisits = document.getElementById('roi-range-visits');
  
  const sliderStoresVal = document.getElementById('roi-slider-stores');
  const sliderVisitsVal = document.getElementById('roi-slider-visits');
  
  const costPhysicalEl = document.getElementById('roi-cost-physical');
  const costDigitalEl = document.getElementById('roi-cost-digital');
  
  const savingsValEl = document.getElementById('roi-savings-val');
  const savingsTimeEl = document.getElementById('roi-savings-time');

  // ROI Calculator core logic
  function calculateOperativeSavings() {
    const activeStores = parseInt(rangeStores.value);
    const visitsPerMonth = parseInt(rangeVisits.value);
    
    sliderStoresVal.textContent = activeStores;
    sliderVisitsVal.textContent = visitsPerMonth;
    
    // Total visits/orders handled per month
    const totalVisits = activeStores * visitsPerMonth;
    
    // Cost of a physical human visit = Bs. 15.00
    // Includes: wages/commissions, vehicle transport, administrative verification
    const costPerPhysicalVisit = 15.00;
    const monthlyPhysicalCost = totalVisits * costPerPhysicalVisit;
    
    // Cost of a digital AI order = Bs. 0.50
    // LLaMA 3.1 runs locally on local GPU server (license-free) + basic hosting
    const costPerDigitalOrder = 0.50;
    const monthlyDigitalCost = totalVisits * costPerDigitalOrder;
    
    // Savings calculation
    const monthlySavingsBs = monthlyPhysicalCost - monthlyDigitalCost;
    
    // Visita física promedio dura 30 minutos (traslado + atención) = 0.5 horas
    const hoursSaved = totalVisits * 0.5;
    
    // Update DOM fields
    if (costPhysicalEl) costPhysicalEl.textContent = `Bs. ${monthlyPhysicalCost.toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (costDigitalEl) costDigitalEl.textContent = `Bs. ${monthlyDigitalCost.toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (savingsValEl) savingsValEl.textContent = `Bs. ${monthlySavingsBs.toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (savingsTimeEl) savingsTimeEl.textContent = `Equivale a ${hoursSaved.toLocaleString('es-BO')} horas de visita física y traslado ahorradas al mes`;
  }

  if (rangeStores) rangeStores.addEventListener('input', calculateOperativeSavings);
  if (rangeVisits) rangeVisits.addEventListener('input', calculateOperativeSavings);
  
  calculateOperativeSavings(); // trigger calculations once on load


  // Init Slide Deck View
  updateSlides();
});
